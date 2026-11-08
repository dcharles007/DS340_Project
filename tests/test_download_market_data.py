import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('download', Path(__file__).resolve().parents[1] / 'scripts/download_market_data.py')
download = importlib.util.module_from_spec(spec)
spec.loader.exec_module(download)

class DownloadTests(unittest.TestCase):
    def test_range_intersection_and_labels(self):
        source = b'observation_date,SP500,NASDAQ100,DJIA\n2023-12-29,1,2,3\n2024-01-02,10.25,20.125,30.75\n2024-01-03,,21,31\n2024-01-04,11,.,32\n'
        rows, excluded = download.clean_csv(source, '2024-01-01', '2024-01-03')
        self.assertEqual(len(rows), 3)
        self.assertEqual({r['index'] for r in rows}, {'SP500','NASDAQ100','DOW'})
        self.assertEqual(next(r['close'] for r in rows if r['index']=='NASDAQ100'), '20.125')
        self.assertEqual(excluded, [{'date':'2024-01-03','missing_series':['SP500']}])

    def test_duplicate_and_invalid_values(self):
        for body in ['2024-01-02,1,2,3\n2024-01-02,1,2,3\n', '2024-01-02,0,2,3\n', '2024-01-02,nan,2,3\n']:
            with self.assertRaises(ValueError):
                download.clean_csv(('observation_date,SP500,NASDAQ100,DJIA\n'+body).encode(),'2024-01-01','2024-01-03')

if __name__ == '__main__':
    unittest.main()
