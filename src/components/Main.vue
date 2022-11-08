<template>
  <div class="box">
    <video id="video" autoplay></video>
  </div>
</template>

<script>
 export default {
   name: 'HelloWorld',
   props: {
     msg: String
   },
   mounted() {
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
</style>
