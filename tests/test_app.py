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

if __name__ == '__main__':
    unittest.main()
