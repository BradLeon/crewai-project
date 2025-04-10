# 在 src/social_media_auto_comment/tools/image_cache.py 中实现
import base64
import os
import hashlib
import requests
import logging
from pathlib import Path
from imagekitio import ImageKit
      # 安装阿里云OSS SDK: pip install oss2
import oss2
#from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# 替换为你的 ImageKit 配置
IMAGEKIT_PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY")
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY")
IMAGEKIT_URL_ENDPOINT = "https://upload.imagekit.io/api/v1/files/upload"

imagekit = ImageKit(
    public_key=IMAGEKIT_PUBLIC_KEY,
    private_key=IMAGEKIT_PRIVATE_KEY,
    url_endpoint = IMAGEKIT_URL_ENDPOINT
)


class ImageCDNTool:
    def __init__(self, cache_dir="data/image_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        logging.info(f"图像缓存目录已初始化: {cache_dir}")
    

    def get_cached_image_path(self, url: str) -> Path:
        """获取图片的缓存路径"""
        cache_dir = Path(os.getcwd()) / "image_cache"
        cache_dir.mkdir(exist_ok=True)
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return cache_dir / f"image_{url_hash}.png"
    
    def get_image_filename(self, url: str) -> str:
        """获取图片的缓存路径"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"image_{url_hash}.png"


    def get_cached_imageB64(self, url):
        '''
        获取缓存图片的base64编码
        '''
        # 创建URL的哈希作为文件名
        cache_path = self.get_cached_image_path(url)
        print(f"缓存路径: {cache_path}")
        # 如果缓存存在，直接返回
        if os.path.exists(cache_path):
            logging.info(f"使用缓存图像: {url}")
            with open(cache_path, 'rb') as f:
                image_data = f.read()
                b64_image = base64.b64encode(image_data).decode("utf-8")

                return b64_image

        # 否则下载并缓存
        try:
            logging.info(f"下载图像: {url}")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(response.content)
                    b64_image = base64.b64encode(response.content).decode("utf-8")
                    print(f"重新缓存图像: {url}")
                    return b64_image
        except Exception as e:
            logging.error(f"缓存图像失败: {str(e)}")
            print(f"缓存图像失败: {str(e)}")
        # 返回None表示获取失败
        return None
    
    def get_image_cdn_url(self, url):
        '''
        上传图片到CDN,并返回CDN的(公开)url
        '''
     
        # 获取图片的base64编码
        b64_image = self.get_cached_imageB64(url)

        image_filename = self.get_image_filename(url)
        print(f"image_filename: {image_filename}")
        
        #print(f"after b64_image encode")
        
        if b64_image is not None:
            # 上传图片到CDN（目前使用ImageKit.io,20GB免费）
            print(f"start upload image to ImageKit.io")
            
            upload_response = imagekit.upload(
            file=b64_image,
            file_name=image_filename,
            )
            print(f"upload_response: {upload_response}")
            try:
                cdn_url = upload_response.get("response").get("url")
            except Exception as e:
                logging.error(f"未获取到CDN图像链接: {str(e)}")
                print(f"未获取到CDN图像链接: {str(e)}")
                #返回原始的url
                return url
            
            return cdn_url
        
        return url

    def get_image_oss_url(self, url):
        '''
        上传图片到阿里云OSS,并返回CDN的(公开)url
        '''
        # 获取阿里云OSS配置
        OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
        OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
        OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")
        OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "oss-cn-shanghai.aliyuncs.com")
        
     
        # 获取图片的base64编码
        b64_image = self.get_cached_imageB64(url)
        if b64_image is None:
            return url
            
        image_filename = self.get_image_filename(url)
        logging.info(f"准备上传图像到阿里云OSS: {image_filename}")
        
        try:
            
            # 初始化阿里云OSS客户端
            auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
            bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)
            
            # 将base64解码为二进制
            image_content = base64.b64decode(b64_image)
            
            # 上传到OSS，使用原始文件名
            object_name = f"images/{image_filename}"
            result = bucket.put_object(object_name, image_content)
            
            # 检查上传结果
            if result.status == 200:
                # 生成公共访问URL
                cdn_url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT}/{object_name}"
                logging.info(f"成功上传到阿里云OSS: {cdn_url}")
                return cdn_url
            else:
                logging.error(f"上传到阿里云OSS失败，状态码: {result.status}")
                return url
                
        except ImportError:
            logging.error("未安装oss2库，请使用pip install oss2安装")
            return url
        except Exception as e:
            logging.error(f"上传到阿里云OSS时发生错误: {str(e)}")
            return url
