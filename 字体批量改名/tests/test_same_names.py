import tempfile
import unittest
from pathlib import Path
from fontTools.ttLib import TTFont, newTable
from font_renamer.core.same_names import scan_same_names, clean_name_groups


def font(path, name, version):
    f=TTFont(); f['name']=newTable('name'); f['name'].names=[]
    for i,value in ((4,name),(5,version),(2,'Regular')):
        f['name'].setName(value,i,3,1,0x0804)
    f.save(path); f.close()


class SameNameTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        font(self.root/'a.ttf','测试字体','Version 1')
        font(self.root/'b.ttf','测试字体','Version 2')
        font(self.root/'c.ttf','其他字体','Version 1')

    def scan(self):
        return scan_same_names(str(self.root),['.ttf'],True)[0]

    def test_internal_names_and_version_comparison(self):
        groups=self.scan(); self.assertEqual(len(groups),1)
        self.assertEqual([m.version for m in groups[0].members],['Version 1','Version 2'])
        self.assertEqual(groups[0].keep,'')
        self.assertNotEqual(groups[0].members[0].digest,groups[0].members[1].digest)

    def test_unconfirmed_group_not_cleaned(self):
        self.assertEqual(clean_name_groups(self.scan(),lambda _:self.fail('unconfirmed')),0)

    def test_user_can_keep_second_version(self):
        group=self.scan()[0]; group.keep=group.members[1].path; group.status='待清理'
        trash=self.root/'trash';trash.mkdir()
        self.assertEqual(clean_name_groups([group],lambda p:Path(p).rename(trash/Path(p).name)),1)
        self.assertTrue((self.root/'b.ttf').exists());self.assertTrue((trash/'a.ttf').exists())
        self.assertTrue((self.root/'c.ttf').exists())

    def test_changed_keep_blocks_clean(self):
        group=self.scan()[0];group.keep=group.members[0].path;group.status='待清理'
        Path(group.keep).write_bytes(b'changed')
        self.assertEqual(clean_name_groups([group],lambda _:self.fail('changed keeper')),0)
        self.assertTrue((self.root/'b.ttf').exists())

    def test_same_filename_different_internal_names(self):
        child=self.root/'child';child.mkdir();font(child/'c.ttf','另一字体','Version 3')
        groups=self.scan();self.assertEqual(len(groups),2)
        self.assertEqual(sum(len(g.members) for g in groups),4)

    def test_recycle_failure_retains_files(self):
        group=self.scan()[0];group.keep=group.members[0].path;group.status='待清理'
        def fail(_):raise PermissionError('locked')
        self.assertEqual(clean_name_groups([group],fail),0)
        self.assertTrue((self.root/'b.ttf').exists());self.assertIn('失败',group.status)
