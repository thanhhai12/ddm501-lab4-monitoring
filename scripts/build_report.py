"""Build the three-page submission analysis from saved real HTTP measurements."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

BASE = Path(__file__).resolve().parents[1]
EVIDENCE = BASE / 'docs/evidence'
FONT = Path('/System/Library/Fonts/Supplemental')
pdfmetrics.registerFont(TTFont('ArialVN', str(FONT / 'Arial.ttf')))
pdfmetrics.registerFont(TTFont('ArialVNBold', str(FONT / 'Arial Bold.ttf')))
styles = {
    'title': ParagraphStyle('title', fontName='ArialVNBold', fontSize=22, leading=27,
                            textColor=colors.HexColor('#16324f'), spaceAfter=16),
    'h': ParagraphStyle('h', fontName='ArialVNBold', fontSize=13, leading=17,
                        textColor=colors.HexColor('#16324f'), spaceBefore=10, spaceAfter=7),
    'body': ParagraphStyle('body', fontName='ArialVN', fontSize=10, leading=15, spaceAfter=9),
    'small': ParagraphStyle('small', fontName='ArialVN', fontSize=8, leading=11, spaceAfter=5),
}
profiles = {name: json.loads((EVIDENCE / f'{name}.json').read_text())
            for name in ['normal', 'drifted-0.05', 'drifted', 'unfair']}
states = {name: value['checkpoints'][-1] for name, value in profiles.items()}
flow = []
md = ['# Lab 4 - Giám sát và triển khai hệ thống ML\n',
      'DDM501 | GitHub: thanhhai12 | Ngày thực nghiệm: 03/10/2026 (UTC+7)\n']

def para(text, style='body'):
    flow.append(Paragraph(escape(text), styles[style]))
    md.append(text+'\n')

def table(rows, widths, font_size=9):
    wrapped = [[Paragraph(escape(str(c)), ParagraphStyle('cell', fontName='ArialVN',
                 fontSize=font_size, leading=font_size+3)) for c in row] for row in rows]
    t = Table(wrapped, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eff7')),
        ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#c4d0dc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 7),
        ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    flow.extend([t, Spacer(1, 10)])
    md.append('| '+' | '.join(str(c) for c in rows[0])+' |\n')
    md.append('| '+' | '.join('---' for _ in rows[0])+' |\n')
    for row in rows[1:]: md.append('| '+' | '.join(str(c) for c in row)+' |\n')
    md.append('\n')

para('Lab 4: Giám sát hệ thống ML', 'title')
para('DDM501 · GitHub: thanhhai12 · Thực nghiệm 03/10/2026, UTC+7', 'small')
para('1. Cách thực hiện và kết quả', 'h')
para('Lab 4 tiếp nối API credit risk của Lab 1 và pipeline của Lab 2. Đề Lab 3 dùng bài toán MovieLens; Lab 4 quay lại credit risk theo starter. Hoàn thành đủ 13 tác vụ, chạy API, Prometheus, Grafana và node-exporter bằng Docker Compose. Prometheus thu được up=1; API có trạng thái healthy.')
para('Dữ liệu là 30.000 dòng mô phỏng do scripts/make_dataset.py tạo, seed 501, đúng schema 23 biến của UCI; đây không phải dữ liệu UCI thật. Model HistGradientBoosting và preprocessing nằm trong một pipeline. Reference được đóng băng từ 24.000 dòng train; test giữ riêng 6.000 dòng. Sáu biến được chia bin theo quantile, biên ngoài mở và epsilon=1e-4.')
para('Mỗi profile gửi 400 yêu cầu HTTP thật, cùng mẫu nền và seed 501. Khởi động lại riêng API giữa các lần chạy để xóa window; reference và model giữ nguyên. Chụp checkpoint mỗi 50 yêu cầu, delay 0,15 giây, tất cả 400/400 phản hồi HTTP 200 trong mỗi profile. Window tối đa 2.000 dòng; chỉ công bố thống kê khi đạt 200, nhóm fairness có ít nhất 30 dòng.')
rows=[['Profile','Điểm TB','REVIEW','DECLINE','Max PSI','Gap (đpt)']]
for name,d in profiles.items():
 s=states[name]
 rows.append([name, f"{d['mean_score']:.4f}",f"{d['decisions'].get('REVIEW',0)/4:.2f}%",
              f"{d['decisions'].get('DECLINE',0)/4:.2f}%",f"{s['drift_score']:.4f}",
              f"{s['fairness_gap']*100:.2f}"])
table(rows,[105,70,70,70,85,111])
para('Baseline normal: PSI=0,0301, gap=1,88 điểm phần trăm, DECLINE=8,00%. Đây là mức ổn định để so sánh. Full drift và unfair đều làm tăng từ chối, nhưng tác động giữa các nhóm rất khác nhau. Các số liệu được đọc từ JSON của chính những lần chạy này; không sao chép bảng kết quả mẫu trong đề.')
para('Kiểm chứng: 79 test pass, coverage app=91,52% (gate 85%). promtool test rules báo SUCCESS. CI GitHub kiểm tra Python, rules, Compose và stack có metric tới Prometheus. Logs, coverage XML và ảnh thật lưu trong docs/evidence.', 'small')
flow.append(PageBreak())
para('2. Tín hiệu nào chuyển động trước?', 'title')
para('Ở drift nhẹ (strength=0,05), payment_ratio dẫn đầu: cuối 400 yêu cầu, PSI của biến này=0,1885, so với 0,0131 ở normal; max PSI tăng 0,1584 và vào vùng moderate. Trong cùng phép so sánh, điểm trung bình chỉ tăng 0,008223; REVIEW từ 14,25% xuống 14,00%, DECLINE từ 8,00% lên 8,50%. Output và quyết định đã đổi một ít, nhưng input drift vượt ngưỡng cảnh báo sớm khi thay đổi kinh doanh còn nhỏ.')
para('Checkpoint đầu đủ mẫu là 200 yêu cầu: ở drift nhẹ, max PSI=0,2313, payment_ratio=0,2313 và utilisation_ratio=0,1313; mean score=0,2278 so với normal 0,2200 ở cùng mốc. DECLINE vẫn 5,00% ở cả hai. Do đó tín hiệu đầu vượt ngưỡng quy định là input drift, không phải tỷ lệ từ chối. Dưới 200, sufficient_data=false: số 0 không được diễn giải thành ổn định.')
para('Thứ tự này là thứ tự phát hiện trong thực nghiệm có checkpoint, không chứng minh mọi biến đổi ngoài đời đều bắt đầu từ input. PSI có nhiễu mẫu: trong drift nhẹ, mốc 250/300 tạm vượt 0,25 rồi về 0,1885 khi đủ 400. Khoảng for: 15m tránh coi một dao động ngắn là sự cố kéo dài.')
para('3. Tín hiệu nào sẽ phát cảnh báo?', 'h')
table([
 ['Profile','Điều kiện vượt ngưỡng cuối run','Nếu duy trì đủ lâu'],
 ['normal','Không có ngưỡng ML bất thường','Không có drift/fairness alert'],
 ['drifted-0.05','PSI > 0,10','ModerateFeatureDrift: warning sau 15m'],
 ['drifted','PSI > 0,25; DECLINE > 20%','Drift critical sau 15m; decision warning sau 30m'],
 ['unfair','PSI > 0,25; gap > 0,10; DECLINE > 20%','Drift critical sau 15m; fairness critical sau 20m; decision warning sau 30m'],
], [95,175,241], 8.5)
para('Các lần chạy chỉ khoảng một phút, chưa chứng minh alert firing sau đủ for:. Bảng là suy luận có điều kiện nếu số đo duy trì; promtool kiểm chứng firing/non-firing theo chuỗi thời gian giả lập, gồm độ trễ và baseline ổn định. Stack chưa cấu hình Alertmanager gửi thông báo ra ngoài, nên “critical” là mức severity trong Prometheus, chưa phải một trang báo gọi người trực.')
para('PredictionErrorsRising cần lỗi model >0,1/s trong 5m; dữ liệu traffic không có lỗi. Không suy ra rằng latency hay SHAP alert luôn tắt: cần đo các histogram riêng; explanation không được gộp vào thời gian scoring. Metrics dùng counter cho tổng, gauge cho trạng thái, histogram cho phân phối và Info cho danh tính model.', 'small')
flow.append(PageBreak())
para('4. Tín hiệu nào chỉ ra nguyên nhân?', 'title')
para('Full drift có PSI=4,2510, cao hơn unfair=0,3526 trong các lần chạy này; không ép hai giá trị thành “tương tự” như mô tả khái quát trong đề. Cả hai đều ở vùng significant, và scalar này không chỉ ra nhóm nào chịu tác động. Panel PSI theo feature và selection rate theo nhóm mới phân biệt được hai tình huống.')
para('Full drift làm payment_ratio=4,2510, utilisation_ratio=3,0921, LIMIT_BAL=2,0426, AGE=1,7084. Selection rate của nhóm SEX=1 là 86,90%, SEX=2 là 83,14%, gap chỉ 3,76 đpt: phần lớn dân số dịch chuyển. Unfair giữ AGE và LIMIT_BAL gần baseline, nhưng max_delay=0,3526, payment_ratio=0,2879, PAY_0=0,2791. Nhóm SEX=1 tăng từ 23,45% lên 93,79%, SEX=2 giữ 21,57%; gap=72,22 đpt. Vì thế fairness panel chỉ rõ thay đổi tập trung vào một nhóm.')
para('Ảnh Grafana thật sau 400 yêu cầu mỗi profile (normal / drifted / unfair):', 'small')
images=[]
for name in ['normal','drifted','unfair']:
 image=Image(str(EVIDENCE/f'grafana-{name}.jpg'),width=150,height=150*853/319)
 images.append(image)
t=Table([images],colWidths=[170,170,171]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]));flow.append(t)
flow.append(Spacer(1,8))
para('Hành động: kiểm tra lỗi upstream và feature trước khi retrain; với unfair, phân tích riêng nhóm và thay đổi nguồn hồ sơ. PSI là đơn biến, gap không chứng minh phân biệt đối xử; dữ liệu mô phỏng và window theo số lượng không cho phép suy luận nhân quả hay accuracy thực tế. SHAP giải thích model, không giải thích nguyên nhân xã hội.', 'small')

def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#c4d0dc'))
    canvas.line(42,36,553,36)
    canvas.setFont('ArialVN',8)
    canvas.setFillColor(colors.HexColor('#61758a'))
    canvas.drawString(42,24,'DDM501 | Lab 4 | thanhhai12 | Số liệu và ảnh từ thực nghiệm thực tế')
    canvas.drawRightString(553,24,str(doc.page))

out=BASE/'docs/REPORT.pdf'
SimpleDocTemplate(str(out),pagesize=A4,rightMargin=42,leftMargin=42,topMargin=38,
                  bottomMargin=48,title='DDM501 Lab 4 - Monitoring analysis',author='thanhhai12').build(
                      flow,onFirstPage=footer,onLaterPages=footer)
(BASE/'docs/REPORT.md').write_text('\n'.join(md)+'''\n## Ảnh và nguồn kiểm chứng\n
![Normal](evidence/grafana-normal.jpg)
![Drift nhẹ](evidence/grafana-drifted-mild.jpg)
![Drifted](evidence/grafana-drifted.jpg)
![Unfair](evidence/grafana-unfair.jpg)
![Fairness panel](evidence/grafana-unfair-fairness.jpg)

- Số liệu: evidence/normal.json, drifted-0.05.json, drifted.json, unfair.json.
- Logs: evidence/pytest.txt, promtool.txt, github-ci.json và github-ci-log.txt.
- Model: evidence/training.txt; reference: ../models/reference.json.
- CI: https://github.com/thanhhai12/ddm501-lab4-monitoring/actions
''')
print(out)
