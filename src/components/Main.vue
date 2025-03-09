<template>
  <div class="box">
    <video ref="video" class="mirrored" autoplay></video>
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

     // Delay camera initialization to give page more loading time
     setTimeout(() => this.initCamera(), 300);
   },
   beforeDestroy() {
     this.releaseCamera();
   },
   methods: {
     initCamera() {
       if (this.initializingCamera) return;
       
       this.initializingCamera = true;
       this.initAttempts++;
       this.errorMessage = null;
       
       const video = this.$refs.video;
       this.releaseCamera();
       
       // Set timeout
       const timeoutPromise = new Promise((_, reject) => {
         setTimeout(() => reject(new Error("Camera access timed out")), 5000);
       });
       
       Promise.race([this.accessCamera(video), timeoutPromise])
         .then(() => {
           this.initializingCamera = false;
         })
         .catch(err => {
           console.error("Failed to initialize camera:", err);
           this.errorMessage = `Cannot access camera: ${err.message || 'Unknown error'}`;
           this.initializingCamera = false;
           
           if (this.initAttempts < this.maxAttempts) {
             setTimeout(() => this.initCamera(), 1000);
           }
         });
     },
     
     async accessCamera(video) {
       // Short delay and check if API exists
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         await new Promise(resolve => setTimeout(resolve, 50));
       }
       
       // Try to request permissions if still not available
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         try {
           await this.pyobject.request_camera_permission();
           await new Promise(resolve => setTimeout(resolve, 50));
         } catch (e) {
           console.error("Failed to request permission:", e);
         }
       }
       
       // Try to access camera
       if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
         try {
           const stream = await navigator.mediaDevices.getUserMedia({ video: true });
           this.videoStream = stream;
           video.srcObject = stream;
           await video.play().catch(e => console.error("Video playback failed:", e));
           return;
         } catch (err) {
           console.warn("Camera access failed:", err.name, err.message);
         }
       }

       throw new Error("Could not access camera");
     },
     
     releaseCamera() {
       if (this.videoStream) {
         try {
           this.videoStream.getTracks().forEach(track => track.stop());
           this.videoStream = null;
           
           if (this.$refs.video && this.$refs.video.srcObject) {
             this.$refs.video.srcObject = null;
           }
         } catch (e) {
           console.error("Error releasing camera resources:", e);
         }
       }
     },
     
     async capture() {
       try {
         if (!this.videoStream) {
           console.error("No active camera stream, cannot take photo");
           this.errorMessage = "Reinitializing camera...";
           this.initCamera();
           return;
         }
         
         const base64String = await this.captureVideoFrame(this.$refs.video);
         this.pyobject.save_screenshot(base64String);
       } catch (error) {
         console.error("Photo capture error:", error);
       }
     },

     async captureVideoFrame(videoElement) {
       return new Promise((resolve, reject) => {
         const canvas = document.createElement("canvas");
         canvas.width = videoElement.videoWidth;
         canvas.height = videoElement.videoHeight;

         const ctx = canvas.getContext("2d");
         ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

         canvas.toBlob(blob => {
           if (!blob) {
             reject(new Error("Failed to create image"));
             return;
           }
           
           const reader = new FileReader();
           reader.onloadend = () => resolve(reader.result);
           reader.onerror = () => reject(new Error("Failed to convert image"));
           reader.readAsDataURL(blob);
         }, "image/png");
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
 
 video {
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
