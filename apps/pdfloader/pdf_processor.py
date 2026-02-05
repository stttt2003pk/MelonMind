import os
import logging
from typing import List, Dict, Generator, Optional
from dataclasses import dataclass
import PyPDF2
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class PDFChunkData:
    """PDF分块数据结构"""
    content: str
    page_number: int
    chunk_index: int
    metadata: Dict


class PDFProcessor:
    """PDF文件处理器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化PDF处理器
        
        Args:
            chunk_size (int): 分块大小
            chunk_overlap (int): 分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, file_path: str) -> List[Dict[str, any]]:
        """
        从PDF文件中提取文本
        
        Args:
            file_path (str): PDF文件路径
            
        Returns:
            List[Dict]: 包含每页文本和页码的列表
        """
        pages_data = []
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text.strip():  # 只保存有内容的页面
                            pages_data.append({
                                'page_number': page_num,
                                'text': text.strip(),
                                'word_count': len(text.split())
                            })
                    except Exception as e:
                        logger.warning(f"提取第{page_num}页文本时出错: {str(e)}")
                        continue
                        
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF文件不存在: {file_path}")
        except Exception as e:
            raise Exception(f"读取PDF文件失败: {str(e)}")
            
        if not pages_data:
            raise ValueError("PDF文件中没有可提取的文本内容")
            
        return pages_data
    
    def chunk_text(self, pages_data: List[Dict[str, any]]) -> Generator[PDFChunkData, None, None]:
        """
        对PDF文本进行分块处理
        
        Args:
            pages_data (List[Dict]): 页面数据列表
            
        Yields:
            PDFChunkData: 分块数据
        """
        chunk_index = 0
        
        for page_data in pages_data:
            page_number = page_data['page_number']
            text = page_data['text']
            
            # 使用LangChain的文本分割器进行智能分块
            chunks = self.text_splitter.split_text(text)
            
            for chunk_content in chunks:
                if chunk_content.strip():  # 只处理非空分块
                    yield PDFChunkData(
                        content=chunk_content.strip(),
                        page_number=page_number,
                        chunk_index=chunk_index,
                        metadata={
                            'page_number': page_number,
                            'chunk_size': len(chunk_content),
                            'word_count': len(chunk_content.split()),
                            'source_file': 'pdf'
                        }
                    )
                    chunk_index += 1
    
    def process_pdf(self, file_path: str) -> Generator[PDFChunkData, None, None]:
        """
        完整的PDF处理流程：提取文本 -> 分块
        
        Args:
            file_path (str): PDF文件路径
            
        Yields:
            PDFChunkData: 分块数据
        """
        # 验证文件
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
            
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("文件必须是PDF格式")
        
        # 提取文本
        logger.info(f"开始处理PDF文件: {file_path}")
        pages_data = self.extract_text_from_pdf(file_path)
        logger.info(f"提取到 {len(pages_data)} 页有效文本")
        
        # 分块处理
        chunk_count = 0
        for chunk_data in self.chunk_text(pages_data):
            yield chunk_data
            chunk_count += 1
            
        logger.info(f"PDF处理完成，共生成 {chunk_count} 个分块")


class PDFMetadataExtractor:
    """PDF元数据提取器"""
    
    @staticmethod
    def get_pdf_metadata(file_path: str) -> Dict[str, any]:
        """
        提取PDF文件元数据
        
        Args:
            file_path (str): PDF文件路径
            
        Returns:
            Dict: 文件元数据
        """
        try:
            stat = os.stat(file_path)
            
            metadata = {
                'file_path': file_path,
                'file_size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
            }
            
            # 提取PDF特定信息
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata.update({
                    'page_count': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted,
                })
                
                # 尝试提取文档信息
                if pdf_reader.metadata:
                    metadata.update({
                        'title': getattr(pdf_reader.metadata, 'title', None),
                        'author': getattr(pdf_reader.metadata, 'author', None),
                        'subject': getattr(pdf_reader.metadata, 'subject', None),
                        'creator': getattr(pdf_reader.metadata, 'creator', None),
                        'producer': getattr(pdf_reader.metadata, 'producer', None),
                    })
                    
        except Exception as e:
            logger.error(f"提取PDF元数据失败: {str(e)}")
            metadata = {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'page_count': 0,
                'error': str(e)
            }
            
        return metadata