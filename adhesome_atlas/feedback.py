import streamlit as st
from urllib.parse import urlencode,quote

def feedback_panel():
    st.subheader('Comments & feedback')
    st.write('Share a catalogue correction, interpretation, suggestion, or question with the Atlas curator. Include a protein accession, orthogroup, or source file when relevant.')
    with st.form('atlas_feedback_form'):
        kind = st.selectbox('Message type', ['Comment or correction', 'Feedback or suggestion', 'Scientific query'])
        subject_detail = st.text_input('Protein, orthogroup, or topic (optional)', max_chars=120)
        sender = st.text_input('Your name (optional)', max_chars=100)
        reply_to = st.text_input('Your email for a reply (optional)', max_chars=200)
        message = st.text_area('Your message', max_chars=2000, height=170)
        prepare = st.form_submit_button('Prepare email draft')
    if prepare:
        if not message.strip():
            st.error('Enter a comment, suggestion, or question to prepare the email draft.')
        else:
            subject = 'Schisto-Adhesome Atlas · ' + kind
            if subject_detail.strip():
                subject += ' · ' + subject_detail.strip()
            body = '\n'.join([
                f'Message type: {kind}',
                f'Topic: {subject_detail.strip() or "Not specified"}',
                f'Name: {sender.strip() or "Not provided"}',
                f'Reply email: {reply_to.strip() or "Not provided"}',
                '', message.strip(),
            ])
            mailto = 'mailto:evansasamoahadu@gmail.com?' + urlencode({'subject': subject, 'body': body}, quote_via=quote)
            st.success('Your draft is ready. Open it in your email app, review it, and send it.')
            st.markdown(f'[Open email draft addressed to evansasamoahadu@gmail.com]({mailto})')
    st.markdown('### Direct queries')
    st.markdown('For scientific queries or correspondence, email [evansasamoahadu@gmail.com](mailto:evansasamoahadu@gmail.com).')
    st.caption('The Atlas does not store or send form entries. The email draft opens in your own mail app.')
