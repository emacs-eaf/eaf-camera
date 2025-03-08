<template>
  <div class="box">
    <video id="video" ref="video" class="mirrored" autoplay></video>
    <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
  </div>
</template>

<script>
 import { QWebChannel } from "qwebchannel";

 export default {
   name: 'HelloWorld',
   props: {
     msg: String
   },
   data() {
     return {
       videoStream: null,
       errorMessage: null,
       initializingCamera: false,
       initAttempts: 0,
       maxAttempts: 3
     };
   },
   created() {
     // eslint-disable-next-line no-undef
     new QWebChannel(qt.webChannelTransport, channel => {
       window.pyobject = channel.objects.pyobject;
       this.pyobject = window.pyobject;
     });
   },
   mounted() {
     window.capture = this.capture;
     window.releaseCamera = this.releaseCamera;
     window.retryCamera = this.initCamera;

     // 延迟初始化摄像头，给页面加载更多时间
     setTimeout(() => {
       this.initCamera();
     }, 300);
   },
   beforeDestroy() {
     // 组件销毁时释放资源
     this.releaseCamera();
   },
   methods: {
     initCamera() {
       if (this.initializingCamera) {
         console.log("摄像头正在初始化中，请稍候...");
         return;
       }
       
       this.initializingCamera = true;
       this.initAttempts++;
       console.log(`初始化摄像头... (第 ${this.initAttempts} 次尝试)`);
       this.errorMessage = null;
       
       var video = document.getElementById('video');

       // 确保之前的流已经释放
       this.releaseCamera();
       
       // 创建一个超时Promise，并使用Promise.race确保不会无限等待
       const timeoutPromise = new Promise((_, reject) => {
         setTimeout(() => reject(new Error("获取摄像头超时")), 5000);
       });
       
       // 使用Promise.race来处理可能的超时情况
       Promise.race([
         this.detectAndUseCamera(video),
         timeoutPromise
       ])
         .then(() => {
           this.initializingCamera = false;
         })
         .catch(err => {
           console.error("初始化摄像头失败:", err);
           this.errorMessage = `无法访问摄像头: ${err.message || '未知错误'}`;
           this.initializingCamera = false;
           
           // 如果尝试次数小于最大次数，自动重试
           if (this.initAttempts < this.maxAttempts) {
             console.log(`摄像头初始化失败，${1000}ms 后自动重试...`);
             setTimeout(() => {
               this.initCamera();
             }, 1000);
           }
         });
     },
     
     async detectAndUseCamera(video) {
       // 尝试多种方法获取摄像头流
       
       console.log("浏览器信息:", navigator.userAgent);
       console.log("检查mediaDevices是否存在:", !!navigator.mediaDevices);
       console.log("检查getUserMedia是否存在:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
       
       // 先尝试延迟检测，给浏览器更多时间初始化API
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         console.log("API尚未准备好，等待500ms后重试...");
         await new Promise(resolve => setTimeout(resolve, 500));
         
         // 再次检查API是否可用
         console.log("延迟后重新检查mediaDevices是否存在:", !!navigator.mediaDevices);
         console.log("延迟后重新检查getUserMedia是否存在:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
       }
       
       // 检查是否完全没有摄像头API
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         console.error("浏览器不支持现代摄像头API，尝试请求权限...");
         
         // 尝试通过请求权限来激活API
         try {
           await this.pyobject.request_camera_permission();
           
           // 再次检查API是否可用
           console.log("权限请求后，检查API状态...");
           console.log("- mediaDevices存在:", !!navigator.mediaDevices);
           console.log("- getUserMedia存在:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
           
           // 额外延迟，让API有时间初始化
           await new Promise(resolve => setTimeout(resolve, 500));
           
           // 再次检查API是否已变为可用
           if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
             console.log("权限请求后，API变为可用");
           } else {
             console.error("权限请求后，API仍不可用");
           }
         } catch (e) {
           console.error("请求权限失败:", e);
         }
       }
       
       // 方法1: 标准 mediaDevices.getUserMedia
       if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
         console.log("尝试使用标准 navigator.mediaDevices.getUserMedia...");
         try {
           const stream = await navigator.mediaDevices.getUserMedia({ video: true });
           this.handleStream(stream, video);
           return;
         } catch (err) {
           console.warn("标准方法失败:", err.name, err.message);
           // 继续尝试其他方法
         }
       }
       
       // 方法2: 旧版 getUserMedia
       const oldGetUserMedia = navigator.getUserMedia || 
                              navigator.webkitGetUserMedia || 
                              navigator.mozGetUserMedia || 
                              navigator.msGetUserMedia;
       
       if (oldGetUserMedia) {
         console.log("尝试使用旧版 getUserMedia...");
         return new Promise((resolve, reject) => {
           oldGetUserMedia.call(navigator, 
             { video: true }, 
             stream => {
               this.handleStream(stream, video);
               resolve();
             },
             err => {
               console.warn("旧版方法失败:", err);
               reject(new Error("所有方法均失败"));
             }
           );
         });
       }
       
       // 方法3: 宽松约束
       if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
         console.log("尝试使用宽松约束...");
         try {
           const stream = await navigator.mediaDevices.getUserMedia({ 
             video: { 
               width: { ideal: 640 },
               height: { ideal: 480 },
               frameRate: { ideal: 15 }
             }
           });
           this.handleStream(stream, video);
           return;
         } catch (err) {
           console.warn("宽松约束方法失败:", err);
         }
       }
       
       // 所有方法都失败
       throw new Error("浏览器不支持任何摄像头访问方法");
     },
     
     handleStream(stream, video) {
       console.log("成功获取摄像头流");
       this.videoStream = stream;
       video.srcObject = stream;
       try {
         video.play();
       } catch (e) {
         console.error("视频播放失败:", e);
       }
     },
     
     releaseCamera() {
       console.log("释放摄像头资源...");
       if (this.videoStream) {
         try {
           this.videoStream.getTracks().forEach(track => {
             track.stop();
             console.log(`轨道 ${track.kind} 已停止`);
           });
           this.videoStream = null;
           
           // 清除视频元素的源
           const video = document.getElementById('video');
           if (video && video.srcObject) {
             video.srcObject = null;
           }
           
           console.log("摄像头资源已释放");
         } catch (e) {
           console.error("释放摄像头资源时出错:", e);
         }
       } else {
         console.log("没有活动的摄像头流需要释放");
       }
     },
     
     async capture() {
       try {
         if (!this.videoStream) {
           console.error("没有活动的摄像头流，无法拍照");
           
           // 尝试重新初始化摄像头
           this.errorMessage = "正在重新初始化摄像头...";
           this.initCamera();
           return;
         }
         
         const videoBlob = await this.captureVideoFrameAsBlob(this.$refs.video, "image/png");
         const base64String = await this.blobToBase64(videoBlob);
         this.pyobject.save_screenshot(base64String);
       } catch (error) {
         console.error("拍照错误:", error);
       }
     },

     async captureVideoFrameAsBlob(videoElement, mimeType = "image/png") {
       return new Promise((resolve, reject) => {
         const canvas = document.createElement("canvas");
         canvas.width = videoElement.videoWidth;
         canvas.height = videoElement.videoHeight;

         const ctx = canvas.getContext("2d");
         ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

         canvas.toBlob((blob) => {
           if (blob) {
             resolve(blob);
           } else {
             reject(new Error("创建Blob对象失败"));
           }
         }, mimeType);
       });
     },

     async blobToBase64(blob) {
       return new Promise((resolve, reject) => {
         const reader = new FileReader();
         reader.onloadend = () => {
           resolve(reader.result);
         };
         reader.onerror = () => {
           reject(new Error("Blob转Base64失败"));
         };
         reader.readAsDataURL(blob);
       });
     }
   }
 }
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
 .box {
   width: 100%;
   height: 100%;
   position: relative;
 }
 
 #video {
   width: 100%;
   height: 100%;
 }

 .mirrored {
   transform: scaleX(-1);
 }
 
 .error-message {
   position: absolute;
   top: 50%;
   left: 50%;
   transform: translate(-50%, -50%);
   background-color: rgba(255, 0, 0, 0.7);
   color: white;
   padding: 15px;
   border-radius: 5px;
   z-index: 1000;
   text-align: center;
   max-width: 80%;
 }
</style>
