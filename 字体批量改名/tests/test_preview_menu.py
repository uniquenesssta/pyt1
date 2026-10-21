import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from font_renamer.ui.preview_actions import PreviewActionsMixin


class PreviewMenuTests(unittest.TestCase):
    def make_app(self,region='cell',row='a',selection=('a',)):
        tree=Mock()
        tree.identify_region.return_value=region
        tree.identify_row.return_value=row
        tree.selection.return_value=selection
        return SimpleNamespace(tree=tree,preview_menu=Mock(),busy=False,_context_plan=object(),_preview_rows={'a':object(),'b':object()})

    def test_selected_row_opens_without_changing_selection(self):
        app=self.make_app()
        PreviewActionsMixin.open_preview_menu(app,SimpleNamespace(x=10,y=20,x_root=100,y_root=200))
        app.preview_menu.tk_popup.assert_called_once_with(100,200)
        app.tree.selection_set.assert_not_called()
        self.assertIs(app._context_plan,app._preview_rows['a'])

    def test_blank_header_unselected_and_busy_do_not_open(self):
        for region,row,selection,busy in [('nothing','',('a',),False),('heading','a',('a',),False),('cell','b',('a',),False),('cell','a',(),False),('cell','a',('a',),True)]:
            with self.subTest(region=region,row=row,selection=selection,busy=busy):
                app=self.make_app(region,row,selection);app.busy=busy
                PreviewActionsMixin.open_preview_menu(app,SimpleNamespace(x=10,y=20,x_root=100,y_root=200))
                app.preview_menu.tk_popup.assert_not_called()
                self.assertIsNone(app._context_plan)
                app.tree.selection_set.assert_not_called()
