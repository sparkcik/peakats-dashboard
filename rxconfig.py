import reflex as rx

config = rx.Config(
    app_name="peakats_fresh",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)