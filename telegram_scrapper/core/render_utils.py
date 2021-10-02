PROCESSING_MESSAGE = "Processando, volte mais tarde."


def render_video_player(video_url):
    return (
        f"<video controls><source src=\"{video_url}\""
        f" type=\"video/mp4\">Navegador não suporta, acesse {video_url}.</video><br>"
    )


def render_audio_player(audio_url):
    return (
        "<audio controls preload=\"metadata\"><source"
        f" src=\"{audio_url}\" type=\"audio/mpeg\">Navegador não suporta,"
        f" acesse {audio_url}.</audio><br>"
    )


def render_image(image_url):
    return f'<a href="{image_url}" target="_blank"><img src="{image_url}" /></a><br>'


def render_document():
    return (
        '<span style="color: red;">(documentos ainda não são suportados para'
        ' visualização)</span>'
    )


def render_message(msg):
    html_output = (
        f" <strong>{msg.group}</strong> {msg.sent_at.strftime('%d/%m/%Y')}"
        f"<a href='/dashboard/core/message/{msg.id}'> (detalhes)</a>"
    )
    html_output += '<div class="message">'

    html_output += (
        (
            render_video_player(msg.video_url)
            if msg.video_url
            else f'<span style="color: red;">{PROCESSING_MESSAGE}</span><br>'
        )
        if msg.video
        else ''
    )

    html_output += (
        (
            render_audio_player(msg.audio_url)
            if msg.audio_url
            else f'<span style="color: red;">{PROCESSING_MESSAGE}</span><br>'
        )
        if msg.audio
        else ''
    )

    html_output += (
        (
            render_image(msg.photo_url)
            if msg.photo_url
            else f'<span style="color: red;">{PROCESSING_MESSAGE}</span><br>'
        )
        if msg.photo_url
        else ''
    )

    html_output += msg.message if msg.message else ''

    html_output += render_document() if msg.document else ''

    html_output += f'<div class="date">{msg.sent_at.strftime("%H:%M")}</div>'

    html_output += '</div>'
    return html_output
