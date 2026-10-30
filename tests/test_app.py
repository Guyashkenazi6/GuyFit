"""Browser acceptance tests. Run: uv run --with playwright python -m unittest discover -s tests -v"""
import json
import os
import shutil
import threading
import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT / 'PulseFit/dist')))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        engine = os.environ.get('BROWSER', 'chromium')
        options = {'headless': True}
        if engine == 'chromium' and os.environ.get('SYSTEM_CHROMIUM'):
            options['executable_path'] = shutil.which('chromium')
            options['args'] = ['--no-sandbox']
        cls.browser = getattr(cls.pw, engine).launch(**options)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()

    def setUp(self):
        self.context = self.browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(10000)
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.dialog_handler = lambda d: d.accept()
        self.page.on('dialog', self.dialog_handler)
        self.page.goto(self.url)
        self.page.wait_for_function("typeof initUpgrade === 'function'")

    def tearDown(self):
        self.context.close()
        self.assertEqual(self.errors, [])

    def start(self):
        self.page.locator('[data-start="0"]').click()

    def complete_set(self):
        self.page.locator('[data-field="weight"]').first.fill('25')
        self.page.locator('[data-field="reps"]').first.fill('10')
        self.page.locator('[data-check]').first.click()

    def test_workout_timer_navigation_and_reload(self):
        self.start()
        self.assertEqual(self.page.locator('.workout-exercise').count(), 1)
        self.assertTrue(self.page.locator('.workout-photo').is_visible())
        self.complete_set()
        self.assertTrue(self.page.locator('#timerDock').is_visible())
        self.assertTrue(self.page.locator('#timerDock').evaluate("e=>e.classList.contains('minimized')"))
        self.page.locator('#timerDismiss').click()
        self.page.locator('#timerPause').click()
        self.assertIsNotNone(self.page.evaluate('rest.remaining'))
        self.page.locator('#timerAdd').click()
        self.page.locator('#timerPause').click()
        end = self.page.evaluate('rest.endAt')
        self.page.locator('#timerDismiss').click()
        self.page.locator('#nextExercise').click()
        self.assertEqual(self.page.evaluate('rest.endAt'), end)
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.active.cursor'), 1)
        self.assertEqual(self.page.evaluate('state.active.exercises[0].logs[0].weight'), '25')
        self.assertEqual(self.page.evaluate('rest.endAt'), end)
        self.page.evaluate('rest.endAt=Date.now()-1000;drawTimer()')
        self.assertTrue(self.page.locator('#timerDock').is_hidden())

    def test_replacement_preserves_completed_sets_and_plan(self):
        self.start()
        old = self.page.evaluate('state.active.exercises[0].id')
        plan = self.page.evaluate('JSON.stringify(state.week)')
        self.complete_set()
        self.page.locator('#replaceActive').click()
        chosen = self.page.locator('[data-replace-id]').evaluate_all(f'els=>els.find(e=>+e.dataset.replaceId!=={old}).dataset.replaceId')
        self.page.locator(f'[data-replace-id="{chosen}"]').click()
        self.assertEqual(self.page.evaluate('state.active.archived[0].id'), old)
        self.assertEqual(self.page.evaluate('state.active.archived[0].logs.length'), 1)
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), plan)
        self.assertFalse(self.page.evaluate('state.active.exercises[0].logs[0].done'))
        self.page.locator('#finishWorkout').click()
        self.assertEqual(self.page.evaluate('state.history[0].volume'), 250)
        self.assertEqual(self.page.evaluate('state.history[0].sets'), 1)
        self.assertEqual(self.page.evaluate('state.history[0].exercises[0].id'), old)
        self.assertTrue(self.page.locator('#timerDock').is_hidden())

    def test_validation_and_legacy_migration(self):
        self.start()
        self.page.locator('[data-check]').first.click()
        self.assertFalse(self.page.evaluate('state.active.exercises[0].logs[0].done'))
        self.assertTrue(self.page.evaluate("(()=>{try{validateState({history:[],active:{}});return false}catch{return true}})()"))
        self.page.evaluate("localStorage.setItem(STORE_KEY,JSON.stringify({week:null,active:null,startedAt:null,history:[{title:'ישן',date:'2026-10-20T10:00:00Z',duration:40,volume:900,sets:10}]}))")
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.history[0].volume'), 900)
        self.assertTrue(self.page.evaluate("!!localStorage.getItem('pulsefit-before-v2')"))

    def test_backup_round_trip_and_invalid_import(self):
        self.start()
        self.complete_set()
        with self.page.expect_download() as download:
            self.page.locator('[data-target="stats"]').click()
            self.page.locator('#exportBackup').click()
        data = json.loads(Path(download.value.path()).read_text())
        self.assertEqual(data['state']['active']['exercises'][0]['logs'][0]['weight'], '25')
        self.page.evaluate('state.active.exercises[0].logs[0].weight="99";save()')
        self.page.locator('#importBackup').set_input_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
        self.page.wait_for_function('state.active?.exercises[0].logs[0].weight === "25"')
        self.page.locator('[data-target="stats"]').click()
        self.page.locator('#importBackup').set_input_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"format":"pulsefit-backup","version":2,"state":{}}'})
        self.assertEqual(self.page.evaluate('state.active.exercises[0].logs[0].weight'), '25')

    def test_offline_and_no_horizontal_overflow(self):
        self.page.evaluate('navigator.serviceWorker.ready')
        self.page.reload()
        self.page.wait_for_function('!!navigator.serviceWorker.controller')
        self.start()
        self.complete_set()
        self.context.set_offline(True)
        self.page.reload()
        self.assertTrue(self.page.locator('.workout-photo').is_visible())
        self.assertEqual(self.page.evaluate('state.active.exercises[0].logs[0].weight'), '25')
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_corrupt_storage_is_not_overwritten(self):
        self.page.evaluate("localStorage.setItem(STORE_KEY,'not-json')")
        self.page.reload()
        self.assertEqual(self.page.evaluate('localStorage.getItem(STORE_KEY)'), 'not-json')
        self.assertTrue(self.page.locator('.load-warning').is_visible())

    def test_permanent_replacement_requires_checkbox(self):
        self.start()
        old = self.page.evaluate('state.active.exercises[0].id')
        self.page.locator('#replaceActive').click()
        self.page.locator('#replacePermanent').check()
        chosen = self.page.locator('[data-replace-id]').evaluate_all(f'els=>els.find(e=>+e.dataset.replaceId!=={old}).dataset.replaceId')
        self.page.locator(f'[data-replace-id="{chosen}"]').click()
        self.assertEqual(self.page.evaluate('state.week[0].exercises[0].id'), int(chosen))

    def test_legacy_catalog_wheel_migration(self):
        self.page.evaluate("generateWeek();state.week[2].exercises[0]={...EXERCISES[45],sets:4,reps:'8–10'};delete state.week[2].exercises[0].cue;save()")
        self.page.reload()
        self.assertFalse(self.page.evaluate('!!window.pulsefitLoadError'))
        self.assertEqual(self.page.evaluate('state.week[2].exercises[0].equipment'), 'גלגל בטן')
        self.assertTrue(self.page.evaluate('!!state.week[2].exercises[0].cue'))

    def test_failed_save_does_not_end_workout(self):
        self.start()
        self.complete_set()
        self.page.evaluate("()=>{Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError')};return true}")
        self.page.locator('#finishWorkout').click()
        self.assertTrue(self.page.evaluate('!!state.active'))
        self.assertEqual(self.page.evaluate('state.history.length'), 0)
        self.assertTrue(self.page.locator('#finishModal').evaluate("e=>!e.classList.contains('show')"))

    def test_multiple_replacements_keep_correct_exercise_identity(self):
        self.start()
        first = self.page.evaluate('state.active.exercises[0].id')
        self.complete_set()
        self.page.locator('#replaceActive').click()
        second = self.page.locator('[data-replace-id]').evaluate_all(f'els=>els.find(e=>+e.dataset.replaceId!=={first}).dataset.replaceId')
        self.page.locator(f'[data-replace-id="{second}"]').click()
        self.complete_set()
        self.page.locator('#replaceActive').click()
        self.page.locator(f'[data-replace-id="{first}"]').click()
        self.page.locator('#finishWorkout').click()
        self.assertEqual(self.page.evaluate('state.history[0].sets'), 2)
        self.assertEqual(self.page.evaluate('state.history[0].volume'), 500)
        self.assertEqual(self.page.evaluate('state.history[0].exercises[1].id'), int(second))

    def test_delete_workout_updates_all_stats_and_persists(self):
        self.start()
        self.complete_set()
        self.page.locator('#finishWorkout').click()
        self.page.evaluate("hideModal('finishModal');go('stats')")
        self.assertEqual(self.page.locator('#totalWorkouts').inner_text(), '1')
        self.page.locator('[data-delete-workout]').click()
        self.assertEqual(self.page.evaluate('state.history.length'), 0)
        self.assertEqual(self.page.locator('#totalWorkouts').inner_text(), '0')
        self.assertEqual(self.page.locator('#totalVolume').inner_text(), '0')
        self.assertEqual(self.page.locator('#workoutDetails details').count(), 0)
        self.assertNotIn('25', self.page.locator('#exerciseProgress').inner_text())
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.history.length'), 0)

    def test_delete_legacy_older_workout_preserves_other_records(self):
        self.page.evaluate("state.history=Array.from({length:12},(_,i)=>({title:'ישן '+i,date:new Date().toISOString(),duration:40,volume:100+i,sets:1}));save();go('stats')")
        self.assertEqual(self.page.locator('[data-delete-workout]').count(), 12)
        self.page.locator('[data-delete-workout="10"]').click()
        self.assertEqual(self.page.evaluate('state.history.length'), 11)
        self.assertFalse(self.page.evaluate("state.history.some(h=>h.title==='ישן 10')"))
        self.assertEqual(self.page.evaluate('state.history[10].title'), 'ישן 11')

    def test_cancel_delete_keeps_history(self):
        self.page.evaluate("state.history=[{title:'בדיקה',date:new Date().toISOString(),duration:40,volume:100,sets:1}];save();go('stats')")
        self.page.remove_listener('dialog', self.dialog_handler)
        self.page.on('dialog', lambda d: d.dismiss())
        self.page.locator('[data-delete-workout]').click()
        self.assertEqual(self.page.evaluate('state.history.length'), 1)
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.history.length'), 1)

    def test_delete_save_failure_rolls_back_and_keeps_active_workout(self):
        self.start()
        self.page.evaluate("state.history=[{title:'בדיקה',date:new Date().toISOString(),duration:40,volume:100,sets:1}];save();go('stats')")
        self.page.evaluate("()=>{Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError')};return true}")
        self.page.locator('[data-delete-workout]').click()
        self.assertEqual(self.page.evaluate('state.history.length'), 1)
        self.assertTrue(self.page.evaluate('!!state.active'))
        self.assertEqual(self.page.locator('[data-delete-workout]').count(), 1)
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.history.length'), 1)
        self.assertTrue(self.page.evaluate('!!state.active'))

    def test_legs_catalog_filter_guidance_and_illustrations(self):
        self.assertEqual(self.page.evaluate('EXERCISES.length'), 57)
        self.assertEqual(self.page.locator('#catalogCount').inner_text(), '57 תרגילים')
        self.assertEqual(self.page.evaluate('new Set(EXERCISES.map(e=>e.id)).size'), 57)
        self.assertEqual(self.page.evaluate('EXERCISES.slice(0,48).map(e=>e.id)'), list(range(1,49)))
        self.assertTrue(self.page.evaluate("LEG_EXERCISES.every(e=>e.steps.length===3&&e.primary&&e.secondary&&e.breathing&&e.mistakes&&e.easier)"))
        self.page.evaluate("go('library')")
        self.page.locator('[data-muscle="legs"]').click()
        self.assertEqual(self.page.locator('[data-exercise]').count(), 9)
        for exercise in self.page.evaluate('LEG_EXERCISES'):
            response = self.page.request.get(self.url+'/'+exercise['image'])
            self.assertEqual(response.status, 200)
            self.assertIn('<svg', response.text())
            self.assertTrue(self.page.evaluate("src=>new Promise(resolve=>{let img=new Image();img.onload=()=>resolve(img.naturalWidth>0);img.onerror=()=>resolve(false);img.src=src})", exercise['image']))
            self.page.locator(f'[data-exercise="{exercise["id"]}"]').click()
            self.assertIn('שרירים עיקריים', self.page.locator('#modalCue').inner_text())
            self.assertIn('גרסה קלה', self.page.locator('#modalCue').inner_text())
            self.assertIn(exercise['image'], self.page.locator('#modalVisual').evaluate('e=>getComputedStyle(e).backgroundImage'))
            self.assertEqual(self.page.locator('#modalVisual').evaluate('e=>getComputedStyle(e).backgroundSize'), 'contain')
            self.page.locator('[data-close="exerciseModal"]').click()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_legs_day_preserves_existing_plan_and_blocks_active_edits(self):
        self.page.evaluate('state.week=state.week.slice(0,3);save();renderWeek()')
        original = self.page.evaluate('JSON.stringify(state.week)')
        self.page.locator('#addLegDay').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week.slice(0,3))'), original)
        self.assertEqual(self.page.evaluate('state.week.length'), 4)
        self.page.locator('#addLegDay').click()
        self.assertEqual(self.page.evaluate('state.week.length'), 4)
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.week[3].exercises.map(e=>e.id)'), [49,53,51,54,55])
        self.start()
        before = self.page.evaluate('JSON.stringify(state)')
        self.page.evaluate('addLegDay()')
        self.assertEqual(self.page.evaluate('JSON.stringify(state)'), before)

    def test_legs_workout_backup_restore_and_history(self):
        self.assertEqual(self.page.evaluate('state.week.length'), 4)
        self.page.evaluate('startWorkout(3)')
        self.complete_set()
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.active.exercises[0].id'), 49)
        self.assertEqual(self.page.evaluate('state.active.exercises[0].logs[0].weight'), '25')
        self.page.evaluate("go('stats')")
        with self.page.expect_download() as download:
            self.page.locator('#exportBackup').click()
        data = Path(download.value.path()).read_bytes()
        self.page.evaluate('state.active=null;save()')
        self.page.locator('#importBackup').set_input_files({'name':'legs.json','mimeType':'application/json','buffer':data})
        self.page.wait_for_function('state.active?.exercises[0].id===49')
        self.page.evaluate("go('workout')")
        self.page.locator('#finishWorkout').click()
        self.assertEqual(self.page.evaluate('state.history[0].exercises[0].id'), 49)
        self.assertEqual(self.page.evaluate('state.history[0].volume'), 250)

    def test_add_legs_day_failed_save_rolls_back(self):
        self.page.evaluate("state.week=state.week.slice(0,3);save();renderWeek()")
        original = self.page.evaluate("JSON.stringify(state.week)")
        self.page.evaluate("()=>{Storage.prototype.setItem=function(){throw new DOMException('quota','QuotaExceededError')}}")
        self.page.locator('#addLegDay').click()
        self.assertEqual(self.page.evaluate("JSON.stringify(state.week)"), original)
        self.page.reload()
        self.assertEqual(self.page.evaluate("JSON.stringify(state.week)"), original)

    def test_legs_replacement_from_existing_plan(self):
        self.start()
        self.page.locator('#replaceActive').click()
        self.page.locator('#replaceMuscle').select_option('legs')
        self.assertEqual(self.page.locator('[data-replace-id]').count(), 9)
        self.page.locator('[data-replace-id="53"]').click()
        self.assertEqual(self.page.evaluate('state.active.exercises[0].id'), 53)
        self.page.reload()
        self.assertIn('53.svg', self.page.locator('.workout-photo').evaluate('e=>getComputedStyle(e).backgroundImage'))

    def test_machine_exercises_save_reload(self):
        self.start()
        for exercise_id in (56, 57):
            self.page.locator("#replaceActive").click()
            self.page.locator("#replaceMuscle").select_option("legs")
            self.page.locator(f'[data-replace-id="{exercise_id}"]').click()
            self.assertEqual(self.page.evaluate("state.active.exercises[0].id"), exercise_id)
            self.page.reload()
            self.assertEqual(self.page.evaluate("state.active.exercises[0].id"), exercise_id)
            self.assertIn(f"{exercise_id}.svg", self.page.locator(".workout-photo").evaluate("e=>getComputedStyle(e).backgroundImage"))

    def test_legacy_three_day_plan_is_not_automatically_changed(self):
        self.page.evaluate('state.week=state.week.slice(0,3);save()')
        original = self.page.evaluate('JSON.stringify(state.week)')
        self.page.reload()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), original)
        self.assertFalse(self.page.evaluate('!!window.pulsefitLoadError'))

    def test_pages_subpath_and_offline_legs_assets(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary,'GuyFit').symlink_to(ROOT, target_is_directory=True)
            server = ThreadingHTTPServer(('127.0.0.1',0), partial(QuietHandler,directory=temporary))
            threading.Thread(target=server.serve_forever,daemon=True).start()
            try:
                url = f'http://127.0.0.1:{server.server_port}/GuyFit/PulseFit/dist/'
                self.page.goto(url)
                self.page.evaluate('navigator.serviceWorker.ready')
                self.page.reload()
                self.page.wait_for_function('!!navigator.serviceWorker.controller')
                self.assertEqual(self.page.evaluate('new URL(navigator.serviceWorker.controller.scriptURL).pathname'), '/GuyFit/PulseFit/dist/sw.js')
                self.page.evaluate('startWorkout(3)')
                self.complete_set()
                self.context.set_offline(True)
                self.page.reload()
                self.assertEqual(self.page.evaluate('state.active.exercises[0].logs[0].weight'), '25')
                self.assertTrue(self.page.evaluate("async()=>{let cache=await caches.open('pulsefit-v8');return (await Promise.all(LEG_EXERCISES.map(e=>cache.match(e.image)))).every(Boolean)}"))
                for exercise in self.page.evaluate('LEG_EXERCISES'):
                    self.assertTrue(self.page.evaluate("async path=>{let response=await fetch(path);return response.ok&&(await response.text()).includes('<svg')}",exercise['image']))
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            finally:
                self.context.set_offline(False)
                self.page.goto('about:blank')
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    unittest.main()
