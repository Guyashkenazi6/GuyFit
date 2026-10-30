"""Acceptance coverage for the weekly planner and editable set counts."""
import test_app


class PlannerTests(test_app.AppTests):
    def test_custom_pairs_cancel_and_reload(self):
        original = self.page.evaluate('JSON.stringify(state.week)')
        self.page.locator('#generateBtn').click()
        self.page.locator('[data-draft="0"][data-group="main"]').select_option('back')
        self.page.locator('[data-draft="0"][data-group="secondary"]').select_option('triceps')
        self.page.locator('#closeBuilder').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), original)
        self.page.locator('#generateBtn').click()
        self.page.locator('[data-draft="0"][data-group="main"]').select_option('back')
        self.page.locator('[data-draft="0"][data-group="secondary"]').select_option('triceps')
        self.page.locator('#applyWeek').click()
        self.assertEqual(self.page.evaluate('[...new Set(state.week[0].exercises.map(e=>e.muscle))]'), ['back', 'triceps'])
        self.page.reload()
        self.assertEqual(self.page.evaluate('state.week[0].title'), 'גב + יד אחורית')


    def test_single_muscle_no_duplicate_exercises_and_day_count(self):
        self.page.locator('#generateBtn').click()
        self.page.locator('[data-draft="0"][data-group="main"]').select_option('core')
        self.page.locator('[data-draft="0"][data-group="secondary"]').select_option('core')
        self.page.locator('[data-remove-day="3"]').click()
        self.page.locator('#addDraftDay').click()
        self.page.locator('#applyWeek').click()
        ids = self.page.evaluate('state.week[0].exercises.map(e=>e.id)')
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(self.page.evaluate('[...new Set(state.week[0].exercises.map(e=>e.muscle))]'), ['core'])
        self.assertEqual(self.page.evaluate('state.week.length'), 4)


    def test_completion_toggle_without_fake_history(self):
        self.page.locator('[data-complete="0"]').click()
        self.page.locator('[data-complete="1"]').click()
        self.assertEqual(self.page.evaluate('state.history.length'), 0)
        self.assertIn('2 מתוך 4', self.page.locator('#weeklyProgress').inner_text())
        self.page.reload()
        self.assertEqual(self.page.locator('[data-complete="1"]').get_attribute('aria-pressed'), 'true')
        self.page.locator('[data-complete="0"]').click()
        self.assertEqual(self.page.locator('[data-complete="0"]').get_attribute('aria-pressed'), 'false')


    def test_set_counts_preserve_completed_logs_and_plan(self):
        original = self.page.evaluate('JSON.stringify(state.week)')
        self.start()
        self.complete_set()
        completed = self.page.evaluate('JSON.stringify(state.active.exercises[0].logs[0])')
        count = self.page.locator('.set-row').count()
        self.page.locator('#addSet').click()
        self.assertEqual(self.page.locator('.set-row').count(), count + 1)
        self.page.reload()
        self.assertEqual(self.page.locator('.set-row').count(), count + 1)
        for _ in range(count):
            self.page.locator('#removeSet').click()
        self.assertEqual(self.page.locator('.set-row').count(), 1)
        self.assertTrue(self.page.locator('#removeSet').is_disabled())
        self.assertEqual(self.page.evaluate('JSON.stringify(state.active.exercises[0].logs[0])'), completed)
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), original)
        self.page.locator('#finishWorkout').click()
        self.assertTrue(self.page.evaluate('!!state.week[0].completedAt'))
        self.assertEqual(self.page.evaluate('state.history[0].sets'), 1)


    def test_failed_save_rolls_back_sets_completion_and_week(self):
        previous = self.page.evaluate('JSON.stringify(state.week)')
        self.page.evaluate("() => { Storage.prototype.setItem=()=>{throw Error('quota')}; }")
        self.page.locator('[data-complete="0"]').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), previous)
        self.page.locator('#generateBtn').click()
        self.page.locator('[data-draft="0"][data-group="main"]').select_option('back')
        self.page.locator('#applyWeek').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.week)'), previous)
        self.page.locator('#closeBuilder').click()
        self.page.reload()
        self.start()
        old = self.page.evaluate('JSON.stringify(state.active)')
        self.page.evaluate("() => { Storage.prototype.setItem=()=>{throw Error('quota')}; }")
        self.page.locator('#addSet').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.active)'), old)
        self.page.locator('#removeSet').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.active)'), old)


    def test_builder_mobile_keyboard_and_active_guard(self):
        self.page.locator('#generateBtn').click()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        self.assertTrue(self.page.locator('#weekBuilder').evaluate('e=>e.scrollWidth<=e.clientWidth'))
        self.page.keyboard.press('Escape')
        self.assertFalse(self.page.locator('#weekBuilder').is_visible())
        self.assertEqual(self.page.evaluate('document.activeElement.id'), 'generateBtn')
        self.start()
        self.page.evaluate("go('planner')")
        self.page.locator('#generateBtn').click()
        self.assertFalse(self.page.locator('#weekBuilder').is_visible())
        self.page.locator('[data-complete="0"]').click()
        self.assertFalse(self.page.evaluate('!!state.week[0].completedAt'))


    def test_set_removal_cancel_keeps_entered_values(self):
        self.start()
        count = self.page.locator('.set-row').count()
        self.page.locator('[data-field="weight"]').last.fill('42')
        self.page.remove_listener('dialog', self.dialog_handler)
        self.page.once('dialog', lambda d: d.dismiss())
        self.page.locator('#removeSet').click()
        self.assertEqual(self.page.locator('.set-row').count(), count)
        self.assertEqual(self.page.locator('[data-field="weight"]').last.input_value(), '42')



# Share browser fixtures without rerunning the regression methods.
for _name in dir(test_app.AppTests):
    if _name.startswith('test_'):
        setattr(PlannerTests, _name, None)
