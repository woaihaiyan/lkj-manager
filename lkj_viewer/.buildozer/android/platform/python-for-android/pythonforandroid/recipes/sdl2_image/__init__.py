import os
import sh
from pythonforandroid.logger import shprint
from pythonforandroid.recipe import BootstrapNDKRecipe


class LibSDL2Image(BootstrapNDKRecipe):
    version = '2.8.2'
    url = 'https://github.com/libsdl-org/SDL_image/releases/download/release-{version}/SDL2_image-{version}.tar.gz'
    dir_name = 'SDL2_image'
    patches = ['enable-webp.patch']

    def get_include_dirs(self, arch):
        return [
            os.path.join(self.ctx.bootstrap.build_dir, "jni", "SDL2_image", "include")
        ]

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        
        # 定位到 SDL2_image 的 external 目录
        external_dir = os.path.join(self.get_build_dir(arch), 'external')
        webp_dir = os.path.join(external_dir, 'libwebp')

        # 如果 libwebp 目录不存在，则进行 git clone
        if not os.path.exists(webp_dir):
            print(f'*** libwebp not found in {webp_dir}, cloning it now... ***')
            try:
                shprint(
                    sh.git,
                    'clone',
                    '--branch', 'v1.3.2', # 使用一个稳定的版本
                    '--depth', '1',       # 只下载最新版本以加快速度
                    'https://github.com/webmproject/libwebp.git',
                    webp_dir
                )
                print(f'*** Successfully cloned libwebp ***')
            except Exception as e:
                print(f'*** FAILED to clone libwebp: {e} ***')
                raise e
        else:
            print(f'*** libwebp already exists, skipping download ***')


recipe = LibSDL2Image()
