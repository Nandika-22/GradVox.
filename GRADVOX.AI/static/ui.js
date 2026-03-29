// simple floating particles effect

setInterval(() => {

let particle = document.createElement("div");

particle.className = "particle";

particle.style.left = Math.random()*100+"vw";

particle.style.animationDuration = (Math.random()*3+3)+"s";

document.body.appendChild(particle);

setTimeout(()=>{
particle.remove()
},6000);

},400);