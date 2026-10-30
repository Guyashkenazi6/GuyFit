"""Regression checks for the restored GuyFit identity and contextual shortcut."""
import unittest
import test_app


class ExperienceTests(unittest.TestCase):
    setUpClass = classmethod(test_app.AppTests.setUpClass.__func__)
    tearDownClass = classmethod(test_app.AppTests.tearDownClass.__func__)
    setUp = test_app.AppTests.setUp
    tearDown = test_app.AppTests.tearDown

    def test_next_workout_tracks_completion_and_resumes_without_reset(self):
        self.page.locator('[data-complete="0"]').click()
        title = self.page.evaluate('state.week[1].title')
        self.assertEqual(self.page.locator('#nextWorkoutDetail').inner_text(), title)
        self.page.locator('#nextWorkout').click()
        self.assertEqual(self.page.evaluate('state.active.day'), 1)
        self.page.locator('[data-field="weight"]').first.fill('25')
        self.page.locator('[data-field="reps"]').first.fill('10')
        self.page.locator('[data-check]').first.click()
        before = self.page.evaluate('JSON.stringify(state.active)')
        self.page.locator('[data-target="planner"]').click()
        self.assertEqual(self.page.locator('#nextWorkoutLabel').inner_text(), 'ממשיכים מאיפה שעצרת')
        self.page.locator('#nextWorkout').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.active)'), before)
        self.page.reload()
        self.page.locator('[data-target="planner"]').click()
        self.page.locator('#nextWorkout').click()
        self.assertEqual(self.page.evaluate('JSON.stringify(state.active)'), before)

    def test_completed_week_hides_next_action_and_undo_restores_it(self):
        for button in self.page.locator('[data-complete]').all():
            button.click()
        self.assertTrue(self.page.locator('#nextWorkout').is_hidden())
        self.page.locator('[data-complete="1"]').click()
        self.assertTrue(self.page.locator('#nextWorkout').is_visible())
        self.page.locator('#nextWorkout').click()
        self.assertEqual(self.page.evaluate('state.active.day'), 1)

    def test_reduced_motion_and_keyboard_disclosure(self):
        self.page.emulate_media(reduced_motion='reduce')
        summary = self.page.locator('.day-summary').nth(1)
        summary.focus()
        self.page.keyboard.press('Enter')
        self.assertEqual(summary.get_attribute('aria-expanded'), 'true')
        self.assertEqual(self.page.locator('.day-detail').nth(1).evaluate('e=>getComputedStyle(e).animationName'), 'none')
        self.assertTrue(self.page.evaluate("()=>{let called=false;const old=window.requestAnimationFrame;window.requestAnimationFrame=()=>{called=true};confetti();window.requestAnimationFrame=old;return !called}"))
