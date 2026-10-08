"""Create a compact six-view gallery from already-QA'd, final CAD renders."""
from pathlib import Path
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import argparse
p=argparse.ArgumentParser(); p.add_argument('--renders',type=Path,required=True); p.add_argument('--output',type=Path,required=True); a=p.parse_args()
views=[('hero.png','D2 cloud polish fork'),('controls.png','Control panel intended finish'),('controls-raw.png','Control panel unfilled engraving'),('collar_pinch.png','Lens collar and pinch access'),('rear.png','Rear and grip side access'),('service.png','Illustrative service separation')]
a.output.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(a.output),pagesize=(792,612),pageCompression=1)
c.setTitle('D2 cloud polish visual supplement'); c.setAuthor('dot'); c.setSubject('Final receipt linked CAD views with intended finish and open physical validation'); c.setKeywords('D2, CAD, cloud polish, intended finish, no physical build or test')
for i,(filename,title) in enumerate(views,1):
    path=a.renders/filename
    with Image.open(path) as image:
        assert image.size==(1800,1400),(filename,image.size)
        buf=BytesIO(); image.convert('RGB').save(buf,format='JPEG',quality=93,subsampling=0,optimize=True); buf.seek(0)
        c.bookmarkPage(str(i)); c.addOutlineEntry(title,str(i),level=0,closed=False)
        c.drawImage(ImageReader(buf),18,12,width=756,height=588,preserveAspectRatio=True)
    c.showPage()
c.save()
print(a.output)
