"""真实 XLSX ZIP 和 XLS BIFF8 数据的读取回归测试。"""
import struct
import tempfile
import unittest
from pathlib import Path
from threading import Event
from zipfile import ZipFile
from lottery.data.importing import load_dataset
from lottery.core.models import Cancelled


def xlsx(path, rows, sheets=1):
    from xml.sax.saxutils import escape
    with ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/></Types>')
        z.writestr('xl/workbook.xml', '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="Sheet{i}" sheetId="{i}" r:id="rId{i}"/>' for i in range(1,sheets+1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,sheets+1))+'</Relationships>')
        data=''
        for ri,row in enumerate(rows,1):
            data+=f'<row r="{ri}">'
            for ci,v in enumerate(row):
                ref=f'{chr(65+ci)}{ri}'
                if v is None: continue
                if isinstance(v,str):
                    data+=f'<c r="{ref}" t="inlineStr"><is><t>{escape(v)}</t></is></c>'
                else: data+=f'<c r="{ref}"><v>{v}</v></c>'
            data+='</row>'
        for i in range(1,sheets+1): z.writestr(f'xl/worksheets/sheet{i}.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+data+'</sheetData></worksheet>')


def xls(path):
    def record(code,data=b''): return struct.pack('<HH',code,len(data))+data
    def bof(kind): return record(0x809,struct.pack('<HHHHII',0x600,kind,0x0dbb,0x07cc,0,6))
    bounds=lambda offset: record(0x85,struct.pack('<IBBBB',offset,0,0,5,0)+b'Sheet')
    prefix=bof(5)
    offset=len(prefix)+len(bounds(0))+4
    sheet=bof(0x10)+record(0x200,struct.pack('<IIHHH',0,1,0,8,0))
    for col,value in enumerate([2026001,1,2,3,4,5,6,7]):
        sheet+=record(0x203,struct.pack('<HHHd',0,col,0,value))
    path.write_bytes(prefix+bounds(offset)+record(0x0a)+sheet+record(0x0a))


class ExcelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'history.xlsx'

    def test_xlsx_multiple_sheets_and_validation(self):
        xlsx(self.path, [[2026001,1,2,3,4,5,6,7],['期号','前区'],[],[2026002,1,2,None,4,5,6,7],[2026003,1,2,3,4,36,6,7]],2)
        d=load_dataset(self.path)
        self.assertEqual((len(d.draws),len(d.issues),d.duplicates,d.ignored),(2,6,1,2))
        self.assertEqual(d.draws[1].sheet,'Sheet2')
        self.assertEqual(d.draws[0].issue,'2026001')
        self.assertIn('Sheet1',d.issues[0].reason)

    def test_xls_binary(self):
        p=self.path.with_suffix('.xls'); xls(p)
        d=load_dataset(p)
        self.assertEqual(d.draws[0].ticket.front,(1,2,3,4,5))
        self.assertEqual(d.draws[0].issue,'2026001')

    def test_typo_extension_text_numbers_and_trailing_empty(self):
        p=self.path.with_suffix('.xlxs'); xlsx(p,[['00123','01','02','03','04','05','06','07',None]])
        self.assertEqual(load_dataset(p).draws[0].issue,'00123')

    def test_cancel_and_release(self):
        xlsx(self.path,[[1,2,3,4,5,6,7]])
        event=Event();event.set()
        with self.assertRaises(Cancelled):load_dataset(self.path,event)
        self.path.unlink()

    def test_corrupt_and_empty(self):
        self.path.write_text('broken')
        with self.assertRaises(Exception):load_dataset(self.path)
        xlsx(self.path,[])
        with self.assertRaisesRegex(ValueError,'没有有效'):load_dataset(self.path)

    def test_decimal_formula_and_bool_rejected(self):
        xlsx(self.path,[[1,2,3,4,5,6,7],[1.5,2,3,4,5,6,7],['=1+0',2,3,4,5,6,7],['True',2,3,4,5,6,7]])
        d=load_dataset(self.path)
        self.assertEqual((len(d.draws),len(d.issues)),(1,3))
