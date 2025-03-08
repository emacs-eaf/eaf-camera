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

     // Delay camera initialization to give page more loading time
     setTimeout(() => {
       this.initCamera();
     }, 300);
   },
   beforeDestroy() {
     // Release resources when component is destroyed
     this.releaseCamera();
   },
   methods: {
     initCamera() {
       if (this.initializingCamera) {
         console.log("Camera is initializing, please wait...");
         return;
       }
       
       this.initializingCamera = true;
       this.initAttempts++;
       console.log(`Initializing camera... (Attempt ${this.initAttempts})`);
       this.errorMessage = null;
       
       var video = document.getElementById('video');

       // Ensure previous stream is released
       this.releaseCamera();
       
       // Create a timeout Promise and use Promise.race to ensure we don't wait indefinitely
       const timeoutPromise = new Promise((_, reject) => {
         setTimeout(() => reject(new Error("Camera access timed out")), 5000);
       });
       
       // Use Promise.race to handle possible timeout situations
       Promise.race([
         this.detectAndUseCamera(video),
         timeoutPromise
       ])
         .then(() => {
           this.initializingCamera = false;
         })
         .catch(err => {
           console.error("Failed to initialize camera:", err);
           this.errorMessage = `Cannot access camera: ${err.message || 'Unknown error'}`;
           this.initializingCamera = false;
           
           // Automatically retry if attempt count is less than max
           if (this.initAttempts < this.maxAttempts) {
             console.log(`Camera initialization failed, auto-retrying in ${1000}ms...`);
             setTimeout(() => {
               this.initCamera();
             }, 1000);
           }
         });
     },
     
     async detectAndUseCamera(video) {
       // Try multiple methods to get camera stream
       
       console.log("Browser info:", navigator.userAgent);
       console.log("Checking if mediaDevices exists:", !!navigator.mediaDevices);
       console.log("Checking if getUserMedia exists:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
       
       // First try delayed detection to give browser more time to initialize API
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         console.log("API not ready yet, waiting 500ms before retrying...");
         await new Promise(resolve => setTimeout(resolve, 500));
         
         // Check API availability again
         console.log("After delay, checking if mediaDevices exists:", !!navigator.mediaDevices);
         console.log("After delay, checking if getUserMedia exists:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
       }
       
       // Check if camera API is completely missing
       if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
         console.error("Browser doesn't support modern camera API, trying to request permission...");
         
         // Try to activate API by requesting permission
         try {
           await this.pyobject.request_camera_permission();
           
           // Check API availability again
           console.log("After permission request, checking API status...");
           console.log("- mediaDevices exists:", !!navigator.mediaDevices);
           console.log("- getUserMedia exists:", navigator.mediaDevices ? !!navigator.mediaDevices.getUserMedia : false);
           
           // Extra delay to let API initialize
           await new Promise(resolve => setTimeout(resolve, 500));
           
           // Check if API has become available
           if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
             console.log("After permission request, API became available");
           } else {
             console.error("After permission request, API still unavailable");
           }
         } catch (e) {
           console.error("Failed to request permission:", e);
         }
       }
       
       // Method 1: Standard mediaDevices.getUserMedia
       if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
         console.log("Trying standard navigator.mediaDevices.getUserMedia...");
         try {
           const stream = await navigator.mediaDevices.getUserMedia({ video: true });
           this.handleStream(stream, video);
           return;
         } catch (err) {
           console.warn("Standard method failed:", err.name, err.message);
           // Continue to try other methods
         }
       }
       
       // Method 2: Legacy getUserMedia
       const oldGetUserMedia = navigator.getUserMedia || 
                              navigator.webkitGetUserMedia || 
                              navigator.mozGetUserMedia || 
                              navigator.msGetUserMedia;
       
       if (oldGetUserMedia) {
         console.log("Trying legacy getUserMedia...");
         return new Promise((resolve, reject) => {
           oldGetUserMedia.call(navigator, 
             { video: true }, 
             stream => {
               this.handleStream(stream, video);
               resolve();
             },
             err => {
               console.warn("Legacy method failed:", err);
               reject(new Error("All methods failed"));
             }
           );
         });
       }
       
       // Method 3: Relaxed constraints
       if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
         console.log("Trying relaxed constraints...");
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
           console.warn("Relaxed constraints method failed:", err);
         }
       }
       
       // All methods failed
       throw new Error("Browser doesn't support any camera access method");
     },
     
     handleStream(stream, video) {
       console.log("Successfully obtained camera stream");
       this.videoStream = stream;
       video.srcObject = stream;
       try {
         video.play();
       } catch (e) {
         console.error("Video playback failed:", e);
       }
     },
     
     releaseCamera() {
       console.log("Releasing camera resources...");
       if (this.videoStream) {
         try {
           this.videoStream.getTracks().forEach(track => {
             track.stop();
             console.log(`Track ${track.kind} stopped`);
           });
           this.videoStream = null;
           
           // Clear video element source
           const video = document.getElementById('video');
           if (video && video.srcObject) {
             video.srcObject = null;
           }
           
           console.log("Camera resources released");
         } catch (e) {
           console.error("Error releasing camera resources:", e);
         }
       } else {
         console.log("No active camera stream to release");
       }
     },
     
     async capture() {
       try {
         if (!this.videoStream) {
           console.error("No active camera stream, cannot take photo");
           
           // Try to reinitialize camera
           this.errorMessage = "Reinitializing camera...";
           this.initCamera();
           return;
         }
         
         const videoBlob = await this.captureVideoFrameAsBlob(this.$refs.video, "image/png");
         const base64String = await this.blobToBase64(videoBlob);
         this.pyobject.save_screenshot(base64String);
       } catch (error) {
         console.error("Photo capture error:", error);
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
             reject(new Error("Failed to create Blob object"));
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
           reject(new Error("Failed to convert Blob to Base64"));
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
