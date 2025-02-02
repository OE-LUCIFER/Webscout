"""Constants used by the LitAgent module."""

# Browser versions we support
BROWSERS = {
    "chrome": (48, 120),
    "firefox": (48, 121),
    "safari": (605, 617),
    "edge": (79, 120),
    "opera": (48, 104)
}

# OS versions
OS_VERSIONS = {
    "windows": ["10.0", "11.0"],
    "mac": ["10_15_7", "11_0", "12_0", "13_0", "14_0"],
    "linux": ["x86_64", "i686"],
    "android": ["10", "11", "12", "13", "14"],
    "ios": ["14_0", "15_0", "16_0", "17_0"]
}

# Device types
DEVICES = {
    "mobile": [
        "iPhone", "iPad", "Samsung Galaxy", "Google Pixel",
        "OnePlus", "Xiaomi", "Huawei", "OPPO", "Vivo"
    ],
    "desktop": ["Windows PC", "MacBook", "iMac", "Linux Desktop"],
    "tablet": ["iPad", "Samsung Galaxy Tab", "Microsoft Surface"],
    "console": ["PlayStation 5", "Xbox Series X", "Nintendo Switch"],
    "tv": ["Samsung Smart TV", "LG WebOS", "Android TV", "Apple TV"]
}