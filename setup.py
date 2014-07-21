from distutils.core import setup
setup(
  name = 'lvsync',
  packages = ['lvsync'],
  version = '201407.4',
  description = 'Logical Volume Sync Tool',
  author = 'Yury Taranov',
  author_email = 'yury.taranov@gmail.com',
  url = 'https://github.com/yurytaranov/lvsync',
  download_url = 'https://github.com/yurytaranov/lvsync/tarball/201407.4',
  keywords = ['lvm', 'sync', 'dd'],
  classifiers = [],
  scripts=[
    'scripts/lvsync',
    'scripts/dd-lvsync'
  ]
)