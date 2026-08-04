[app]

# (string) Title of your application
title = Sakina Prayer App

# (string) Package name
package.name = sakinaprayerapp

# (string) Package domain (needed for android packaging)
package.domain = org.sufyan

# (string) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json

# (string) Application versioning
version = 0.1

# (list) Application requirements
# أضف هنا المكتبات التي يستخدمها تطبيقك تفصل بينها فاصلة
requirements = python3,kivy

# (str) Custom source code for main.py
# main.filename = main.py

# (list) Permissions
# أضف الصلاحيات إذا كان تطبيقك يحتاج الإنترنت مثلاً
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) The Android arch to build for
android.archs = arm64-v8a, armeabi-v7a

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with output from commands))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = ignore, 1 = warn, 2 = error)
warn_on_root = 1
