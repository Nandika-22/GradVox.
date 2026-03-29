let recognition
let isListening = false

function speak(text){

let speech = new SpeechSynthesisUtterance(text)
speech.lang = "en-US"
speech.rate = 1

speechSynthesis.speak(speech)

}

function startInterview(){

document.getElementById("question").innerText = questionsData[currentIndex]

speak(questionsData[currentIndex])

}

function startSpeech(){

if(!('webkitSpeechRecognition' in window)){

alert("Your browser does not support Speech Recognition. Please use Google Chrome.")

return

}

recognition = new webkitSpeechRecognition()

recognition.lang = "en-US"
recognition.continuous = true
recognition.interimResults = true

recognition.start()

isListening = true

recognition.onresult = function(event){

let transcript = ""

for(let i = event.resultIndex; i < event.results.length; i++){

transcript += event.results[i][0].transcript

}

document.getElementById("answerBox").value = transcript

}

recognition.onerror = function(event){

console.log("Speech recognition error:", event.error)

}

}

function stopSpeech(){

if(recognition && isListening){

recognition.stop()

isListening = false

}

}

function nextQuestion(){

currentIndex++

document.getElementById("answerBox").value = ""

if(currentIndex < questionsData.length){

document.getElementById("question").innerText = questionsData[currentIndex]

speak(questionsData[currentIndex])

}

if(currentIndex === questionsData.length-1){

document.getElementById("submitBtn").style.display = "inline-block"

}

}

function submitInterview(){

window.location.href = "/result"

}