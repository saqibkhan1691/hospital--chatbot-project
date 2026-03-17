%%writefile "SK/Hospital Chatbot Project/Static/chat.js"
const messagesEl = document.getElementById('messages');
const inp = document.getElementById('inp');
const send = document.getElementById('send');
const nameEl = document.getElementById('name');

function appendMessage(text, who='bot'){
  const d = document.createElement('div');
  d.className = 'msg ' + (who==='user' ? 'user' : 'bot');
  d.innerText = text;
  messagesEl.appendChild(d);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

send.onclick = async () => {
  const txt = inp.value.trim();
  const nm = nameEl.value.trim();
  if(!txt) return;
  appendMessage(txt, 'user');
  inp.value = '';
  appendMessage('...', 'bot');
  try{
    const resp = await fetch('/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: txt, name: nm})
    });
    const j = await resp.json();
    // remove last '...' message
    const nodes = messagesEl.querySelectorAll('.msg.bot');
    if(nodes.length) nodes[nodes.length-1].remove();
    appendMessage(j.response, 'bot');
  }catch(e){
    const nodes = messagesEl.querySelectorAll('.msg.bot');
    if(nodes.length) nodes[nodes.length-1].remove();
    appendMessage('Error connecting to server. Make sure app.py is running.', 'bot');
  }
};

inp.addEventListener("keydown", function(e){
  if(e.key === "Enter") send.click();
});







// // chat.js (final)
// %%writefile "SK/Hospital Chatbot Project/Static/chat.js"
// const messagesEl = document.getElementById('messages');
// const inp = document.getElementById('inp');
// const send = document.getElementById('send');
// const nameEl = document.getElementById('name');
// const typingWrapper = document.getElementById('typing-wrapper');
// const doctorListEl = document.getElementById('doctor-list');
// let isSending=false;

// function appendMessage(text, who='bot'){
//   const m = document.createElement('div');
//   m.className = 'msg ' + (who==='user' ? 'user' : 'bot');
//   const inner = document.createElement('div');
//   inner.className = 'msg-inner';
//   inner.innerText = text;
//   m.appendChild(inner);
//   messagesEl.appendChild(m);
//   messagesEl.scrollTop = messagesEl.scrollHeight;
// }

// function showTyping(){ typingWrapper.style.display='block'; messagesEl.scrollTop = messagesEl.scrollHeight; }
// function hideTyping(){ typingWrapper.style.display='none'; }

// async function loadDoctors(){
//   try{
//     const res = await fetch('/doctors');
//     const docs = await res.json();
//     doctorListEl.innerHTML = '';
//     docs.forEach(d=>{
//       const card = document.createElement('div');
//       card.className = 'doc-card';
//       card.innerHTML = `<img class="doc-logo" src="${d.logo_url}" alt="${d.name}"/>
//                         <div class="doc-meta"><b>${d.name}</b><div><small>${d.specialty} • ${d.gender}</small></div></div>`;
//       card.onclick = ()=> {
//         inp.value = `Book ${d.specialty} with ${d.name} on `;
//         inp.focus();
//       };
//       doctorListEl.appendChild(card);
//     });
//   }catch(e){
//     console.error("doctors load", e);
//   }
// }

// appendMessage("Hi! I'm your hospital assistant. Ask me to book appointments, check symptoms, or show doctors.", "bot");

// async function sendMessage(){
//   if(isSending) return;
//   const txt = inp.value.trim();
//   const nm = nameEl.value.trim();
//   if(!txt) return;
//   isSending=true;
//   appendMessage(txt, 'user');
//   inp.value='';
//   showTyping();
//   try{
//     const resp = await fetch('/chat',{
//       method:'POST',
//       headers:{'Content-Type':'application/json'},
//       body: JSON.stringify({message: txt, name: nm})
//     });
//     const j = await resp.json();
//     setTimeout(()=>{
//       hideTyping();
//       appendMessage(j.response || "No response", 'bot');
//       isSending=false;
//     }, 250);
//   }catch(e){
//     hideTyping();
//     appendMessage('Error connecting to server. Make sure backend is running.', 'bot');
//     isSending=false;
//   }
// }

// send.onclick = sendMessage;
// inp.addEventListener('keydown', e => { if(e.key==='Enter') sendMessage(); });

// function prefill(text){ inp.value = text; inp.focus(); }
// window.addEventListener('load', loadDoctors);
