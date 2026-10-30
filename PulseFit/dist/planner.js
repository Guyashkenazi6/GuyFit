// Weekly composition is a draft until explicitly applied. Existing logs never change.
let weekDraft = [];
let builderReturnFocus = null;
const builder = document.createElement('dialog');
builder.id = 'weekBuilder';
builder.setAttribute('aria-labelledby', 'builderTitle');
document.body.append(builder);

function muscleOptions(selected, optional = false) {
  return (optional ? '<option value="">ללא קבוצה נוספת</option>' : '') +
    Object.entries(MUSCLE_HE).map(([key, name]) => `<option value="${key}" ${key === selected ? 'selected' : ''}>${esc(name)}</option>`).join('');
}

function openWeekBuilder() {
  if (state.active) { toast('סיים את האימון הפעיל לפני שינוי התוכנית'); return; }
  builderReturnFocus = document.activeElement;
  weekDraft = (state.week || []).map(day => {
    const groups = [...new Set(day.exercises.map(e => e.muscle))];
    return { main: groups[0] || 'chest', secondary: groups[1] || '' };
  });
  if (!weekDraft.length) weekDraft = [{ main: 'back', secondary: 'biceps' }];
  renderWeekBuilder();
  builder.showModal();
}

function renderWeekBuilder() {
  builder.innerHTML = `<div class="builder-heading"><p class="kicker">YOUR WEEK. YOUR WAY.</p><button id="closeBuilder" class="icon-btn" aria-label="סגור תכנון">×</button></div>
    <h2 id="builderTitle">מה מתאמנים השבוע?</h2>
    <p class="builder-note">בחר קבוצת שרירים אחת או צמד לכל אימון. זו נקודת פתיחה שאפשר להתאים לך, לא חובה להתאמן בכל יום.</p>
    <div class="draft-days">${weekDraft.map((day, i) => `<fieldset class="draft-day"><legend>אימון ${i + 1}</legend>
      <label>קבוצה ראשית<select data-draft="${i}" data-group="main">${muscleOptions(day.main)}</select></label>
      <label>לשלב עם<select data-draft="${i}" data-group="secondary">${muscleOptions(day.secondary, true)}</select></label>
      <button class="remove-day" data-remove-day="${i}" ${weekDraft.length === 1 ? 'disabled' : ''} aria-label="הסר אימון ${i + 1}">הסר אימון</button></fieldset>`).join('')}</div>
    <button id="addDraftDay" class="ghost-btn" ${weekDraft.length >= 7 ? 'disabled' : ''}>＋ הוסף אימון לשבוע</button>
    <p class="builder-note">עד 7 אימונים. בנייה מחדש מחליפה את התוכנית והסימונים הנוכחיים בלבד. היסטוריית האימונים נשמרת. מומלץ לייצא גיבוי לפני שינוי.</p>
    <p id="builderError" role="alert" hidden></p><button id="applyWeek" class="primary-btn">בנה את השבוע שלי</button>`;
  builder.querySelector('#closeBuilder').onclick = () => builder.close();
  builder.querySelectorAll('select').forEach(select => select.onchange = () => {
    weekDraft[+select.dataset.draft][select.dataset.group] = select.value;
  });
  builder.querySelectorAll('[data-remove-day]').forEach(button => button.onclick = () => {
    weekDraft.splice(+button.dataset.removeDay, 1); renderWeekBuilder();
    builder.querySelector('#addDraftDay').focus();
  });
  builder.querySelector('#addDraftDay').onclick = () => {
    if (weekDraft.length >= 7) return;
    weekDraft.push({ main: 'back', secondary: 'triceps' }); renderWeekBuilder();
    builder.querySelector(`[data-draft="${weekDraft.length - 1}"]`).focus();
  };
  builder.querySelector('#applyWeek').onclick = applyWeekDraft;
}

function exercisesForGroups(main, secondary) {
  const groups = [main, secondary].filter((group, i, all) => group && all.indexOf(group) === i);
  return groups.flatMap((group, i) => {
    const pool = shuffle(EXERCISES.filter(e => e.muscle === group));
    const compound = pool.find(e => e.type === 'מורכב') || pool[0];
    return [compound, ...pool.filter(e => e.id !== compound.id)]
      .slice(0, groups.length === 1 ? 5 : i === 0 ? 4 : 3)
      .map(e => ({ ...e, ...rx(e) }));
  });
}

function applyWeekDraft() {
  if (state.active) { toast('יש אימון פעיל. התוכנית לא שונתה'); return; }
  if (state.week && !confirm('להחליף את התוכנית ואת סימוני הביצוע? היסטוריית האימונים תישמר.')) return;
  const previous = state.week;
  state.week = weekDraft.map((day, i) => ({
    id: i + 1,
    title: [...new Set([day.main, day.secondary].filter(Boolean))].map(g => MUSCLE_HE[g]).join(' + '),
    exercises: exercisesForGroups(day.main, day.secondary)
  }));
  if (!save()) { state.week = previous; const error = builder.querySelector('#builderError'); error.hidden = false; error.textContent = 'השמירה נכשלה. התוכנית הקיימת לא שונתה. בדוק מקום פנוי או ייצא גיבוי.'; error.scrollIntoView({ block: 'nearest' }); return; }
  renderWeek(); builder.close(); toast('השבוע שלך מוכן. מתחילים בצעד אחד ✨');
}

function toggleDayCompletion(index) {
  if (state.active?.day === index) { toast('סיים את האימון הפעיל כדי לסמן אותו כבוצע'); return; }
  const day = state.week[index], previous = day.completedAt;
  if (previous) delete day.completedAt;
  else day.completedAt = new Date().toISOString();
  if (!save()) { if (previous) day.completedAt = previous; else delete day.completedAt; return; }
  renderWeek();
  $(`[data-complete="${index}"]`)?.focus();
  toast(previous ? 'סימון הביצוע בוטל. ההיסטוריה לא השתנתה' : 'סומן כבוצע! הסימון לא מוסיף משקלים או סטים להיסטוריה');
}

function renderWeeklyProgress() {
  const total = state.week?.length || 0;
  const done = (state.week || []).filter(day => day.completedAt).length;
  const percent = total ? Math.round(done / total * 100) : 0;
  $('#weeklyProgress').innerHTML = `<div class="week-ring" style="--progress:${percent}%"><strong>${done}<small> / ${total}</small></strong></div><div><p class="kicker">ההתקדמות בתוכנית</p><h3>${done === total && total ? 'השבוע שלך. הניצחון שלך.' : done ? 'כבר התחלת. ממשיכים קדימה.' : 'כל אימון מתחיל בהחלטה קטנה.'}</h3><p>${done} מתוך ${total} אימונים סומנו כבוצעו</p></div>`;
}

function changeActiveSets(delta) {
  if (!state.active) return;
  const exercise = state.active.exercises[state.active.cursor || 0];
  const previous = structuredClone(exercise);
  if (delta > 0) {
    if (exercise.logs.length >= 100) return;
    exercise.logs.push({ weight: '', reps: '', done: false });
  } else {
    // Remove the last unfinished set, never a completed one.
    if (exercise.logs.length <= 1) return;
    const index = exercise.logs.findLastIndex(set => !set.done);
    if (index < 0) return;
    const row = exercise.logs[index];
    if ((row.weight !== '' || row.reps !== '') && !confirm('להסיר את הסט שלא בוצע? הערכים שהוזנו בו יימחקו.')) return;
    exercise.logs.splice(index, 1);
  }
  exercise.sets = exercise.logs.length;
  if (!save()) { Object.assign(exercise, previous); return; }
  renderActive();
  $(delta > 0 ? '#addSet' : '#removeSet')?.focus();
  toast(delta > 0 ? 'נוסף סט לאימון הנוכחי בלבד' : 'הוסר סט שלא בוצע. הסטים שביצעת נשמרו');
}

builder.addEventListener('close', () => builderReturnFocus?.focus());
$('#generateBtn').onclick = openWeekBuilder;
$('#rerollAll').onclick = openWeekBuilder;
renderWeeklyProgress();
