"""Design acceptance checks using synthetic browser data only."""
import unittest
import test_app


class DesignTests(unittest.TestCase):
    setUpClass = classmethod(test_app.AppTests.setUpClass.__func__)
    tearDownClass = classmethod(test_app.AppTests.tearDownClass.__func__)
    setUp = test_app.AppTests.setUp
    tearDown = test_app.AppTests.tearDown

    def test_original_dark_identity_contrast_and_navigation(self):
        for scheme in ['light', 'dark']:
            self.page.emulate_media(color_scheme=scheme)
            self.assertEqual(self.page.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor'), 'rgb(8, 9, 12)')
            colors = self.page.evaluate("""() => {
                let s=getComputedStyle(document.documentElement);
                return Object.fromEntries(['--text','--muted','--surface','--accent','--success'].map(k=>[k,s.getPropertyValue(k).trim()]));
            }""")
            def luminance(hex_color):
                channels = [int(hex_color[i:i+2], 16)/255 for i in (1, 3, 5)]
                values = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in channels]
                return sum(a*b for a, b in zip(values, [.2126, .7152, .0722]))
            for foreground in ['--text', '--muted', '--accent', '--success']:
                a, b = sorted([luminance(colors[foreground]), luminance(colors['--surface'])])
                self.assertGreaterEqual((b+.05)/(a+.05), 4.5, (scheme, foreground))
            self.page.locator('[data-target="stats"]').click()
            self.assertEqual(self.page.locator('[aria-current="page"]').get_attribute('data-target'), 'stats')
            self.page.locator('[data-target="planner"]').click()
        self.assertEqual(self.page.locator('[aria-current="page"]').count(), 1)

    def test_mobile_desktop_and_large_text_layout(self):
        for width in [320, 390, 768, 1280]:
            self.page.set_viewport_size({'width': width, 'height': 900})
            for view in ['planner', 'workout', 'library', 'stats']:
                self.page.locator('[data-target="'+view+'"]').click()
                self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'), (width, view))
            for item in self.page.locator('.nav-item').all():
                box = item.bounding_box()
                self.assertGreaterEqual(box['width'], 44)
                self.assertGreaterEqual(box['height'], 44)
        self.page.set_viewport_size({'width': 390, 'height': 844})
        self.page.add_style_tag(content='html { font-size: 125%; }')
        self.page.locator('[data-target="planner"]').click()
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        self.page.locator('#generateBtn').click()
        self.assertTrue(self.page.evaluate('document.querySelector("#weekBuilder").scrollWidth<=document.querySelector("#weekBuilder").clientWidth'))

    def test_appearance_update_preserves_active_workout(self):
        self.page.locator('[data-start="0"]').click()
        self.page.locator('[data-field="weight"]').first.fill('25')
        self.page.locator('[data-field="reps"]').first.fill('10')
        self.page.locator('[data-check]').first.click()
        before = self.page.evaluate('JSON.stringify(state)')
        self.page.emulate_media(color_scheme='dark', reduced_motion='reduce')
        self.assertEqual(self.page.evaluate('JSON.stringify(state)'), before)
        self.page.reload()
        self.assertEqual(self.page.locator('[data-field="weight"]').first.input_value(), '25')
        self.assertTrue(self.page.locator('[data-check]').first.evaluate("e=>e.classList.contains('checked')"))

    def test_offline_design_assets(self):
        self.page.evaluate('navigator.serviceWorker.ready')
        self.page.reload()
        self.page.wait_for_function('!!navigator.serviceWorker.controller')
        self.context.set_offline(True)
        self.page.reload()
        self.assertEqual(self.page.title(), 'GuyFit — מתכנן אימונים')
        self.assertTrue(self.page.evaluate("async()=>{let r=await fetch('./apple.css');return r.ok&&(await r.text()).includes('--success: #bdfc63')}"))
        self.assertEqual(self.page.locator('body').evaluate('e=>getComputedStyle(e).backgroundColor'), 'rgb(8, 9, 12)')
