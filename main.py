import flet as ft
import instaloader
import threading
import os
import tempfile

# بررسی پلتفرم
try:
    from android.storage import app_storage_path
    from androidmedia import MediaScanner
    ANDROID = True
except:
    ANDROID = False

# برای یوتیوب
try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except:
    YT_DLP_AVAILABLE = False

def main(page: ft.Page):
    # تنظیمات صفحه برای موبایل
    page.title = "دانلودر حرفه‌ای"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = "#667eea"
    
    # توابع navigation
    def go_to_instagram(e):
        page.clean()
        page.add(instagram_page)
    
    def go_to_youtube(e):
        page.clean()
        page.add(youtube_page)
    
    def go_to_main(e):
        page.clean()
        page.add(main_container)
    
    # تابع دریافت مسیر دانلود
    def get_download_path():
        if ANDROID:
            try:
                path = "/storage/emulated/0/Pictures/Downloader"
                os.makedirs(path, exist_ok=True)
                return path
            except:
                try:
                    path = os.path.join(app_storage_path(), "downloads")
                    os.makedirs(path, exist_ok=True)
                    return path
                except:
                    return "/storage/emulated/0/Download"
        else:
            # برای ویندوز (موقع تست)
            path = os.path.join(tempfile.gettempdir(), "Downloader")
            os.makedirs(path, exist_ok=True)
            return path
    
    # تابع اسکن فایل برای گالری
    def scan_file(file_path):
        if not ANDROID:
            return True  # در ویندوز کاری نمیکنه
            
        try:
            from androidmedia import MediaScanner
            scanner = MediaScanner()
            scanner.scan_file(file_path)
            return True
        except:
            try:
                from android import mActivity
                from android.content import Intent
                from android.net import Uri
                from java.io import File
                
                intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
                intent.setData(Uri.fromFile(File(file_path)))
                mActivity.sendBroadcast(intent)
                return True
            except:
                return False
    
    # تابع دانلود اینستاگرام
    def download_instagram(url):
        try:
            L = instaloader.Instaloader()
            shortcode = url.split("/")[-2]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            download_path = get_download_path()
            L.download_post(post, target=download_path)
            
            # پیدا کردن فایل دانلود شده برای اسکن
            for file in os.listdir(download_path):
                if file.startswith(shortcode):
                    file_path = os.path.join(download_path, file)
                    scan_file(file_path)
                    break
            
            return True, "دانلود با موفقیت انجام شد! ✅"
        except Exception as e:
            return False, f"خطا: {str(e)}"
    
    def start_instagram_download(e):
        if insta_url_field.value:
            insta_progress_bar.visible = True
            insta_progress_bar.value = 0.3
            insta_status_text.value = "در حال پردازش لینک... ⏳"
            page.update()
            
            def download_thread():
                try:
                    insta_progress_bar.value = 0.6
                    insta_status_text.value = "در حال دانلود... ⬇️"
                    page.update()
                    
                    success, message = download_instagram(insta_url_field.value)
                    
                    if success:
                        insta_progress_bar.value = 1.0
                        insta_status_text.value = message
                    else:
                        insta_progress_bar.value = 0
                        insta_status_text.value = message
                        
                    page.open(ft.SnackBar(ft.Text(value=message)))
                        
                except Exception as e:
                    insta_progress_bar.value = 0
                    insta_status_text.value = f"خطای ناشناخته: {str(e)} ❌"
                    page.open(ft.SnackBar(ft.Text(value=f"خطا: {str(e)}")))
                finally:
                    insta_progress_bar.visible = False
                    page.update()
            
            threading.Thread(target=download_thread, daemon=True).start()
            
        else:
            insta_progress_bar.visible = False
            insta_status_text.value = "لطفا لینک را وارد کنید ❌"
            page.update()

    # تابع دانلود یوتیوب
    def download_youtube(url, quality='highest'):
        if not YT_DLP_AVAILABLE:
            return False, "ماژول yt-dlp نصب نیست!"
            
        try:
            if '/shorts/' in url:
                video_id = url.split('/shorts/')[1].split('?')[0]
                url = f'https://www.youtube.com/watch?v={video_id}'
            
            download_path = get_download_path()
            ydl_opts = {
                'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
                'format': 'best[ext=mp4]',
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                
            # اسکن برای گالری
            scan_result = scan_file(file_path)
            
            if scan_result:
                return True, "دانلود کامل شد! در گالری قابل مشاهده است ✅"
            else:
                return True, "دانلود کامل شد! ✅"
                
        except Exception as e:
            return False, f"خطا: {str(e)}"

    def start_youtube_download(e):
        if youtube_url_field.value:
            youtube_progress_bar.visible = True
            youtube_progress_bar.value = 0.3
            youtube_status_text.value = "در حال پردازش... ⏳"
            page.update()

            def download_thread():
                try:
                    success, message = download_youtube(youtube_url_field.value)

                    if success:
                        youtube_progress_bar.value = 1.0
                        youtube_status_text.value = message
                    else:
                        youtube_progress_bar.value = 0
                        youtube_status_text.value = message
                        
                    page.open(ft.SnackBar(ft.Text(value=message)))
                        
                except Exception as e:
                    youtube_progress_bar.value = 0
                    youtube_status_text.value = f"خطای ناشناخته: {str(e)} ❌"
                    page.open(ft.SnackBar(ft.Text(value=f"خطا: {str(e)}")))
                finally:
                    youtube_progress_bar.visible = False
                    page.update()
                    
            threading.Thread(target=download_thread, daemon=True).start()
        else:
            youtube_progress_bar.visible = False
            youtube_status_text.value = "لطفا لینک را وارد کنید ❌"
            page.update()

    # المان‌های صفحه اینستاگرام
    insta_url_field = ft.TextField(
        label="لینک پست یا ویدیو",
        hint_text="https://www.instagram.com/p/...",
        width=page.width * 0.85,
        border_color="#FFFFFF",
        text_align=ft.TextAlign.RIGHT,
        content_padding=ft.padding.all(12),
        prefix_icon=ft.Icons.SEARCH
    )
    
    insta_progress_bar = ft.ProgressBar(
        value=0,
        width=page.width * 0.8,
        height=20,
        color="#E1306C",
        bgcolor="#FFFFFF",
        visible=False
    )
    
    insta_status_text = ft.Text(
        "لینک پست را وارد کنید",
        size=16,
        color="#FFFFFF",
        text_align=ft.TextAlign.CENTER
    )
    
    insta_download_button = ft.ElevatedButton(
        content=ft.Text("شروع دانلود", size=16, color="#FFFFFF"),
        bgcolor="#E1306C",
        width=page.width * 0.8,
        height=50,
        on_click=start_instagram_download,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    # صفحه اینستاگرام
    instagram_page = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=go_to_main
                    ),
                    ft.Text("دانلود از اینستاگرام", size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ft.Container(width=40)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=20, horizontal=16),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Image(
                            src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png",
                            width=80,
                            height=80,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=40,
                        margin=ft.margin.only(bottom=20)
                    ),
                    ft.Text("لینک مورد نظر خود را وارد کنید", size=16, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    insta_url_field,
                    ft.Container(height=20),
                    insta_download_button,
                    ft.Container(height=30),
                    insta_progress_bar,
                    ft.Container(height=15),
                    insta_status_text,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("راهنمای استفاده:", size=14, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            ft.Text("• لینک پost یا ویدیو را کپی کنید", size=12, color="#FFFFFF"),
                            ft.Text("• روی دکمه دانلود کلیک کنید", size=12, color="#FFFFFF"),
                        ], spacing=8),
                        padding=ft.padding.all(16),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=12,
                        margin=ft.margin.symmetric(horizontal=20, vertical=20),
                        width=page.width * 0.9
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=0),
        gradient=ft.LinearGradient(colors=["#667eea", "#764ba2"]),
        expand=True
    )
    
    # المان‌های صفحه یوتیوب
    youtube_url_field = ft.TextField(
        label="لینک ویدیو",
        hint_text="https://www.youtube.com/...",
        width=page.width * 0.85,
        border_color="#FFFFFF",
        text_align=ft.TextAlign.RIGHT,
        content_padding=ft.padding.all(12)
    )
    
    youtube_progress_bar = ft.ProgressBar(
        value=0,
        width=page.width * 0.8,
        height=20,
        color="#FF0000",
        bgcolor="#FFFFFF",
        visible=False
    )
    
    youtube_status_text = ft.Text(
        "لینک ویدیو را وارد کنید",
        size=16,
        color="#FFFFFF",
        text_align=ft.TextAlign.CENTER
    )
    
    youtube_download_button = ft.ElevatedButton(
        content=ft.Text("شروع دانلود", size=16, color="#FFFFFF"),
        bgcolor="#FF0000",
        width=page.width * 0.8,
        height=50,
        on_click=start_youtube_download,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )
    
    # صفحه یوتیوب
    youtube_page = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color="#FFFFFF",
                        icon_size=24,
                        on_click=go_to_main
                    ),
                    ft.Text("دانلود از یوتیوب", size=20, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    ft.Container(width=40)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=ft.padding.symmetric(vertical=20, horizontal=16),
                bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.BLACK)
            ),
            
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Image(
                            src="https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
                            width=80,
                            height=80,
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=40,
                        margin=ft.margin.only(bottom=20)
                    ),
                    ft.Text("لینک مورد نظر خود را وارد کنید", size=16, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    youtube_url_field,
                    ft.Container(height=20),
                    youtube_download_button,
                    ft.Container(height=30),
                    youtube_progress_bar,
                    ft.Container(height=15),
                    youtube_status_text,
                    ft.Container(
                        content=ft.Column([
                            ft.Text("راهنمایی", size=14, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                            ft.Text("• لینک ویدیو را از اپ یوتیوب کپی کنید", size=12, color="#FFFFFF"),
                            ft.Text("• لینک باید با https:// شروع شود", size=12, color="#FFFFFF"),
                        ], spacing=8),
                        padding=ft.padding.all(16),
                        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        border_radius=12,
                        margin=ft.margin.symmetric(horizontal=20, vertical=20),
                        width=page.width * 0.9
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        ], spacing=0),
        gradient=ft.LinearGradient(colors=["#667eea", "#764ba2"]),
        expand=True
    )
    
    # -------------------- صفحه اصلی --------------------
    header = ft.Container(
        content=ft.Column([
            ft.Text("دانلودر حرفه‌ای", size=24, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ft.Text("دانلود آسان و سریع از یوتیوب و اینستاگرام", size=14, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        padding=ft.padding.symmetric(vertical=20, horizontal=10),
        alignment=ft.alignment.center
    )
    
    instagram_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Image(src="https://cdn-icons-png.flaticon.com/512/2111/2111463.png", width=25, height=25),
                ft.Text("اینستاگرام", size=18, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ], spacing=12),
            ft.Container(height=8),
            ft.Text("دانلود عکس، ویدیو و استوری از اینستاگرام", size=13, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
            ft.Container(height=12),
            ft.Container(
                content=ft.Text("انتخاب کنید", size=14, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                bgcolor="#E1306C",
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                border_radius=20,
                alignment=ft.alignment.center,
                width=120,
                on_click=go_to_instagram
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        border_radius=12,
        margin=ft.margin.symmetric(horizontal=16, vertical=8),
        blur=ft.Blur(8, 8, ft.BlurTileMode.MIRROR),
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        width=page.width * 0.9
    )
    
    youtube_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Image(src="https://cdn-icons-png.flaticon.com/512/1384/1384060.png", width=25, height=25),
                ft.Text("یوتیوب", size=18, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
            ], spacing=12),
            ft.Container(height=8),
            ft.Text("دانلود ویدیو و موزیک از یوتیوب", size=13, color="#FFFFFF", text_align=ft.TextAlign.CENTER),
            ft.Container(height=12),
            ft.Container(
                content=ft.Text("انتخاب کنید", size=14, color="#FFFFFF", weight=ft.FontWeight.BOLD),
                bgcolor="#FF0000",
                padding=ft.padding.symmetric(horizontal=20, vertical=10),
                border_radius=20,
                alignment=ft.alignment.center,
                width=120,
                on_click=go_to_youtube
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
        border_radius=12,
        margin=ft.margin.symmetric(horizontal=16, vertical=8),
        blur=ft.Blur(8, 8, ft.BlurTileMode.MIRROR),
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.WHITE)),
        width=page.width * 0.9
    )
    
    footer = ft.Container(
        content=ft.Text("سریع • امن • رایگان", size=12, color="#FFFFFF", weight=ft.FontWeight.BOLD),
        padding=ft.padding.all(16),
        alignment=ft.alignment.center
    )
    
    main_column = ft.Column([
        header,
        instagram_card,
        youtube_card,
        footer
    ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    main_container = ft.Container(
        content=main_column,
        gradient=ft.LinearGradient(colors=["#667eea", "#764ba2"]),
        expand=True,
        padding=ft.padding.only(bottom=20)
    )
    
    page.add(main_container)

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, host="192.168.1.5", port=8553)