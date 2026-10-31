"""Offline tests on exclusively fictional data. Run: python -m unittest discover -s tests -v"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('migrate_admins', ROOT / 'scripts' / 'migrate_admins.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        wb = Workbook()
        ws = wb.active
        ws.append(['username','first_name','last_name','email','site_count','password','legacy_username','mode'])
        ws.append(['new-alice','Alice','Smith','alice@example.invalid',2,'locally-generated-password-1','old-alice','import'])
        ws.append(['bob','Bob','Reader','bob@example.invalid',1,'locally-generated-password-2','', 'import'])
        ws.append(['platformadmin1','Carol','Owner','owner@example.invalid',2,None,'old-admin','manual'])
        self.xlsx = self.path / 'people.xlsx'
        wb.save(self.xlsx)
        self.legacy_file = self.path / 'legacy.jsonl'
        self.target_file = self.path / 'target.jsonl'
        a, b, c = '1'*24, '2'*24, '3'*24
        admins = [('a'*24,'old-alice','alice@example.invalid',[(a,'admin'),(b,'admin')]),
                  ('b'*24,'bob','bob@example.invalid',[(a,'readonly')]),
                  ('c'*24,'old-admin','owner@example.invalid',[(a,'admin'),(b,'admin')])]
        lines = []
        for admin_id, username, email, sites in admins:
            for sid, role in sites:
                lines.append(dict(admin_id=admin_id,admin_name=username,admin_email=email,
                                  site_id=sid,site_name='site-'+sid[0],
                                  site_description='Example site '+sid[0],role=role))
        self.legacy_file.write_text(''.join(json.dumps(x)+'\n' for x in lines)+json.dumps(dict(_export_summary=True,privilege_count=len(lines),admin_count=3,site_count=3))+'\n',encoding='utf8')
        self.target_file.write_text(''.join(json.dumps(dict(site_id=sid, site_name='site-'+sid[0],
                                         site_description='Example site '+sid[0]))+'\n' for sid in [a,b,c])+json.dumps(dict(_export_summary=True,site_count=3))+'\n', encoding='utf8')

    def tearDown(self):
        self.tmp.cleanup()

    def collect(self):
        people = mod.read_people(self.xlsx)
        legacy, role_counts = mod.read_legacy(self.legacy_file)
        target = mod.read_target_sites(self.target_file)
        return mod.prepare(people, legacy, target, {'platformadmin1'}), role_counts

    def test_rename_multisite_readonly_manual(self):
        rows, counts = self.collect()
        self.assertEqual(counts['admin'], 4)
        by_name = {r['key']:r for r in rows}
        self.assertEqual(len(by_name['new-alice']['formulas']), 2)
        self.assertEqual(by_name['new-alice']['formulas'], [f's-{"1"*24}-admin', f's-{"2"*24}-admin'])
        self.assertEqual(by_name['bob']['formulas'], [f's-{"1"*24}-readonly'])
        self.assertEqual(by_name['new-alice']['legacy_username'],'old-alice')
        self.assertFalse([r['reasons'] for r in rows if r['reasons']])
        pending, done = mod.plan(rows, {})
        self.assertEqual(len(pending), 2)
        self.assertFalse(done)

    def test_checkpoint_and_no_secrets(self):
        rows, _ = self.collect()
        account = next(r for r in rows if r['key']=='bob')
        fp = mod.fingerprint(account)
        self.assertNotIn('locally-generated-password-2', fp)
        path = self.path / 'state.json'
        mod.save_state(path, {'bob':{'stage':'created_pending_manual_verification','fingerprint':fp}})
        self.assertNotIn('locally-generated-password-2', path.read_text())
        pending, complete = mod.plan(rows, mod.read_state(path))
        self.assertEqual(len(pending), 1)
        self.assertEqual(len(complete), 1)
        path.write_text(json.dumps({'bob':{'stage':'user_post_uncertain','fingerprint':fp}}))
        with self.assertRaisesRegex(ValueError, 'Never auto-retry'):
            mod.plan(rows, mod.read_state(path))

    def test_target_missing_site_blocks(self):
        lines = self.target_file.read_text().splitlines()
        self.target_file.write_text(lines[0]+'\n'+json.dumps(dict(_export_summary=True,site_count=1))+'\n',encoding='utf8')
        rows, _ = self.collect()
        self.assertTrue(any('Missing target site ID' in reason
                            for r in rows for reason in r['reasons']))

    def test_duplicate_old_mapping_blocks(self):
        people = mod.read_people(self.xlsx)
        people['other'] = dict(people['new-alice'],username='other',legacy_username='old-alice')
        legacy, _ = mod.read_legacy(self.legacy_file)
        target = mod.read_target_sites(self.target_file)
        rows = mod.prepare(people,legacy,target,{'platformadmin1'})
        self.assertTrue(any('Multiple new accounts' in x for r in rows for x in r['reasons']))

    def test_truncated_export_rejected(self):
        lines = self.legacy_file.read_text().splitlines()
        self.legacy_file.write_text('\n'.join(lines[:-1])+'\n',encoding='utf8')
        with self.assertRaisesRegex(ValueError, 'summary line is missing'):
            mod.read_legacy(self.legacy_file)

    def test_admin_owner_protection(self):
        people = mod.read_people(self.xlsx)
        people['admin'] = dict(people['new-alice'],username='admin')
        legacy, _ = mod.read_legacy(self.legacy_file)
        target = mod.read_target_sites(self.target_file)
        rows = mod.prepare(people,legacy,target,{'platformadmin1'})
        self.assertTrue(any('protected target Owner' in x for r in rows for x in r['reasons']))


if __name__ == '__main__':
    unittest.main()
