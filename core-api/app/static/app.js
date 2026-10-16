// Small same-origin demonstration client. Tokens live in memory, not localStorage.
let accessToken = null;
let refreshToken = null;
const notice = document.querySelector('#notice');
const fieldNames = {username:'Имя пользователя',email:'Email',password:'Пароль',password_confirm:'Повтор пароля',code:'Код',github_url:'GitHub'};

function message(text, error=false) {
  notice.textContent = text;
  notice.classList.toggle('error', error);
  notice.hidden = false;
}
function showTab(name) {
  document.querySelectorAll('.auth-form').forEach(f => { f.hidden = f.id !== `${name}-form`; });
  document.querySelectorAll('[data-tab]').forEach(b => b.classList.toggle('selected', b.dataset.tab === name));
  notice.hidden = true;
}
function prefillEmail(email) {
  document.querySelectorAll('.auth-form input[name=email]').forEach(e => {e.value = email;});
}
function explain(detail) {
  const known = {
    'Incorrect email or password':'Неверный email или пароль.',
    'Email already registered':'Этот email уже зарегистрирован.',
    'Username already taken':'Это имя пользователя уже занято.',
    'Email or username already registered':'Email или имя пользователя уже зарегистрированы.',
    'Confirm your email first':'Сначала подтверди email кодом из письма.',
    'Invalid or expired code':'Код неверен или истёк. Запроси новый.',
    'Too many requests. Try later.':'Слишком много попыток. Попробуй через 5 минут.',
    'Invalid or expired token':'Сессия истекла. Войди снова.'
  };
  if (Array.isArray(detail)) return detail.map(e => `${fieldNames[e.loc.at(-1)] || e.loc.at(-1)}: ${e.msg}`).join('\n');
  return known[detail] || detail || 'Не удалось выполнить запрос.';
}
async function api(path, method='GET', body, retry=true) {
  const headers = {'Content-Type':'application/json'};
  if(accessToken) headers.Authorization = `Bearer ${accessToken}`;
  let response;
  try { response = await fetch(`/api/v1${path}`, {method,headers,body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(10000)}); }
  catch { throw Error('Нет подключения. Проверь интернет и повтори попытку.'); }
  if(response.status===401 && refreshToken && retry && path!=='/auth/refresh') {
    try {
      const tokens = await api('/auth/refresh','POST',{refresh_token:refreshToken},false);
      accessToken=tokens.access_token; refreshToken=tokens.refresh_token;
    } catch { accessToken=null;refreshToken=null;throw Error('Сессия истекла. Войди снова.'); }
    return api(path,method,body,false);
  }
  const data = await response.json();
  if(!response.ok) throw Error(explain(data.detail));
  return data;
}
function bindForm(id, handler) {
  const form = document.querySelector(`#${id}-form`);
  form.addEventListener('submit', async event => {
    event.preventDefault();notice.hidden=true;
    const data=Object.fromEntries(new FormData(form));
    if(data.password_confirm!==undefined && data.password!==data.password_confirm) {
      form.elements.password_confirm.setAttribute('aria-invalid','true');
      message('Пароли не совпадают.',true);return;
    }
    const button=form.querySelector('button[type=submit]');button.disabled=true;
    try { await handler(data,form); }
    catch(error) { message(error.message,true); }
    finally { button.disabled=false; }
  });
  form.addEventListener('input', e=>e.target.removeAttribute('aria-invalid'));
}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab)));
bindForm('register', async(data,form)=>{
  await api('/auth/register','POST',data);form.reset();prefillEmail(data.email);showTab('verify');message('Аккаунт создан. Введи код подтверждения.');
});
bindForm('verify', async data=>{
  await api('/auth/verify-email','POST',data);showTab('login');message('Email подтверждён. Теперь можно войти.');
});
bindForm('forgot', async data=>{
  await api('/auth/forgot-password','POST',data);prefillEmail(data.email);showTab('reset');message('Если аккаунт существует, код отправлен.');
});
bindForm('reset', async(data,form)=>{
  await api('/auth/reset-password','POST',data);form.reset();prefillEmail(data.email);showTab('login');message('Пароль изменён. Войди с новым паролем.');
});
bindForm('login', async(data,form)=>{
  const tokens=await api('/auth/login','POST',data);
  accessToken=tokens.access_token;refreshToken=tokens.refresh_token;form.reset();await loadAccount();
});
document.querySelector('#resend').addEventListener('click',async()=>{
  try {
    const email=document.querySelector('#verify-form input[name=email]').value;
    await api('/auth/resend-verification','POST',{email});message('Если подтверждение требуется, новый код отправлен.');
  } catch(e){message(e.message,true);}
});
async function loadAccount(){
  const [user,profile,roles,skills]=await Promise.all([api('/users/me'),api('/profiles/me'),api('/roles'),api('/skills?limit=100')]);
  document.querySelector('#auth').hidden=true;document.querySelector('#account').hidden=false;
  document.querySelector('#account-email').textContent=`${user.username} · ${user.email}`;
  const form=document.querySelector('#profile-form');
  for(const name of ['first_name','last_name','bio','github_url']) form.elements[name].value=profile[name]||'';
  const roleSelect=document.querySelector('#roles');roleSelect.replaceChildren(new Option('Выбери роль',''));
  roles.forEach(r=>roleSelect.add(new Option(r.name,r.id)));roleSelect.value=profile.role_id||'';
  const skillFields=document.querySelector('#skill-fields');skillFields.replaceChildren();
  skills.forEach(skill=>{
    const label=document.createElement('label');label.textContent=skill.name;
    const select=document.createElement('select');select.name=String(skill.id);
    select.add(new Option('Нет','0'));for(let n=1;n<=5;n++) select.add(new Option(String(n),String(n)));
    select.value=profile.skills.find(s=>s.skill_id===skill.id)?.level||0;
    label.append(select);skillFields.append(label);
  });
  await loadProjects();
}
bindForm('profile',async data=>{
  data.role_id=data.role_id?Number(data.role_id):null;data.github_url=data.github_url||null;
  await api('/profiles/me','PATCH',data);message('Профиль сохранён.');
});
bindForm('skills',async data=>{
  const skills=Object.entries(data).filter(([,level])=>Number(level)>0).map(([id,level])=>({skill_id:Number(id),level:Number(level)}));
  await api('/profiles/me/skills','PUT',{skills});message('Навыки сохранены.');await loadProjects();
});
async function loadProjects(){
  const items=await api('/recommendations/projects');const list=document.querySelector('#projects');list.replaceChildren();
  if(!items.length){list.textContent='Пока нет новых проектов. Создай первый через Swagger или вернись позже.';return;}
  for(const item of items){
    const card=document.createElement('article');card.className='project';
    const title=document.createElement('h4');title.textContent=item.project.title;
    const desc=document.createElement('p');desc.textContent=item.project.description;
    const score=document.createElement('small');score.textContent=`Сходство навыков: ${Math.round(item.score*100)}%`;
    const actions=document.createElement('div');
    for(const [label,decision] of [['Интересно','like'],['Пропустить','pass']]){
      const b=document.createElement('button');b.textContent=label;
      b.addEventListener('click',async()=>{b.disabled=true;try{
        const result=await api(`/projects/${item.project.id}/my-swipe`,'PUT',{decision});
        if(result.match)message('Взаимный интерес! Совпадение появилось в списке matches.');
        await loadProjects();
      }catch(e){message(e.message,true);b.disabled=false;}});actions.append(b);
    }
    card.append(title,desc,score,actions);list.append(card);
  }
}
document.querySelector('#reload-projects').addEventListener('click',()=>loadProjects().catch(e=>message(e.message,true)));
document.querySelector('#logout').addEventListener('click',async()=>{
  try{await api('/auth/logout','POST');accessToken=null;refreshToken=null;
    document.querySelector('#account').hidden=true;document.querySelector('#auth').hidden=false;showTab('login');
  }catch(e){message(e.message,true);}
});
fetch('/health',{signal:AbortSignal.timeout(5000)}).then(async r=>{
  if(!r.ok)throw Error();const info=await r.json();document.querySelector('#server-status').textContent='● Сервер работает';
  document.querySelector('#local-hint').hidden=info.environment!=='local'||info.mail!=='outbox';
}).catch(()=>{document.querySelector('#server-status').textContent='● Нет подключения';});
