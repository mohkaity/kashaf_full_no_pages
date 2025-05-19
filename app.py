import streamlit as st
import pandas as pd
from docx import Document
from io import BytesIO
from openai import OpenAI

# ---------- واجهة التطبيق ----------
st.set_page_config(page_title="كشافات علمية من النص الكامل", layout="wide")
st.title("📚 استخراج الكشافات العلمية من نص كامل لشيخ الإسلام ابن تيمية")

# ---------- إدخال البيانات ----------
openai_key = st.text_input("🔐 أدخل مفتاح OpenAI", type="password")
model_choice = st.selectbox("🧠 اختر النموذج", ["gpt-4", "gpt-3.5-turbo"])
uploaded_file = st.file_uploader("📄 ارفع ملف وورد يحتوي على النص الكامل", type=["docx"])

if "excel_output" not in st.session_state:
    st.session_state.excel_output = None

# ---------- استخراج النص الكامل من Word ----------
def extract_full_text(docx_file):
    doc = Document(docx_file)
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return full_text

# ---------- توليد البرومبت ----------
def generate_prompt(text):
    return f"""
أنت محلل نصوص شرعية.

اقرأ النص التالي من كتاب لشيخ الإسلام ابن تيمية، واستخرج المواضع التي تحتوي على كشاف علمي فقط، ضمن التصنيفات التالية:

1. تفسير الآيات
2. شروح الأحاديث
3. الأحكام الحديثية
4. الإجماع
5. الخلاف
6. الترجيح
7. القواعد والضوابط والفروق والتقاسيم
8. المواقف الشخصية

📌 رجاءً أخرج النتائج فقط بصيغة جدول (سطر لكل كشاف) وبهذا التنسيق الدقيق:

مطلع الفقرة | نوع الكشاف | عنوان الكشاف | سبب التصنيف

لا تكتب أي شيء آخر، ولا تدرج سطرًا إلا إذا كان يحتوي كشافًا فعليًا.

النص:
{text}
"""

# ---------- التحليل ----------
def analyze_text_with_gpt(text, model, api_key):
    client = OpenAI(api_key=api_key)
    prompt = generate_prompt(text)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "أنت مساعد ذكي متخصص في تحليل النصوص الشرعية واستخراج الكشافات العلمية منها بدقة."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

# ---------- تحويل النتائج إلى جدول ----------
def parse_response_to_df(response_text):
    rows = []
    lines = response_text.strip().splitlines()

    for line in lines:
        if "|" in line:
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 4:
                rows.append({
                    "مطلع الفقرة": parts[0],
                    "نوع الكشاف": parts[1],
                    "عنوان الكشاف": parts[2],
                    "سبب التصنيف": parts[3]
                })

    return pd.DataFrame(rows)

# ---------- تنفيذ التحليل ----------
if st.button("🚀 تحليل النص") and uploaded_file and openai_key:
    with st.spinner("جاري تحليل النص..."):
        try:
            full_text = extract_full_text(uploaded_file)
            response_text = analyze_text_with_gpt(full_text, model_choice, openai_key)

            st.subheader("🧾 محتوى رد النموذج (للمراجعة):")
            st.code(response_text)

            df = parse_response_to_df(response_text)

            if df.empty:
                st.warning("⚠️ لم يتم العثور على أي كشافات، راجع البرومبت أو تحقق من تنسيق الرد.")
            else:
                # حفظ ملف إكسل
                excel_io = BytesIO()
                df.to_excel(excel_io, index=False)
                st.session_state.excel_output = excel_io

                st.success("✅ تم استخراج الكشافات بنجاح!")
                st.dataframe(df)

        except Exception as e:
            st.error("حدث خطأ أثناء التحليل:")
            st.exception(e)

# ---------- زر التحميل ----------
if st.session_state.excel_output:
    st.download_button(
        label="📥 تحميل ملف Excel",
        data=st.session_state.excel_output.getvalue(),
        file_name="kashafaat.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
