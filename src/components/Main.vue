<template>
  <div class="box">
    <video id="video" ref="video" class="mirrored" autoplay></video>
  </div>
</template>

<script>
 import { QWebChannel } from "qwebchannel";

 export default {
   name: 'HelloWorld',
   props: {
     msg: String
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

     var video = document.getElementById('video');

     // Get access to the camera!
     if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
       // Not adding `{ audio: true }` since we only want video now
       navigator.mediaDevices.getUserMedia({ video: true }).then(function(stream) {
         //video.src = window.URL.createObjectURL(stream);
         video.srcObject = stream;
         video.play();
       });
     }
   },
   methods: {
     async capture() {
       try {
         const videoBlob = await this.captureVideoFrameAsBlob(this.$refs.video, "image/png");
         const base64String = await this.blobToBase64(videoBlob);
         this.pyobject.save_screenshot(base64String);
       } catch (error) {
         console.error("Error capturing video frame as Blob:", error);
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
             reject("Error creating Blob object.");
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
           reject("Error converting Blob to Base64.");
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
 }
 
 #video {
   width: 100%;
   height: 100%;
 }

 .mirrored {
   transform: scaleX(-1);
 }
</style>
