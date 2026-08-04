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
# ملاحظة: إذا كان كودك يستخدم مكتبات إضافية مثل requests لجلب مواقيت الصلاة أضفها هنا
requirements = python3,kivy

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API
android.api = 33

# (int) Minimum API supported
android.minapi = 21

# (str) Android NDK version to use (إصدار مستقر)
android.ndk = 25b

# (str) Android Build Tools version to use (يمنع أخطاء إصدار 37)
android.build_tools_version = 33.0.2

# (str) The Android arch to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Accept SDK licenses automatically
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
