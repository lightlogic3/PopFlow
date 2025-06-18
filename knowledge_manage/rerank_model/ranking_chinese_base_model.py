from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from knowledge_manage.rerank_model.base import BaseRankingModel

class TextRankingModel(BaseRankingModel):
    # 静态变量，用于存储pipeline实例
    _pipeline_instance = None
    _model_id = None
    
    @classmethod
    def initialize(cls, model_dir):
        """
        初始化模型 - 静态方法，只需调用一次
        
        Args:
            model_dir: 模型目录路径
        """
        if cls._pipeline_instance is None:
            cls._model_id = model_dir
            cls._pipeline_instance = pipeline(task=Tasks.text_ranking, model=model_dir, model_revision='v1.1.0')
            return True
        return False
    
    @classmethod
    def rank(cls, inputs):
        """
        使用模型对文本进行排序 - 静态方法，可以直接调用
        
        Args:
            inputs: 包含source_sentence和sentences_to_compare的字典
            
        Returns:
            排序结果
            
        Raises:
            RuntimeError: 如果模型未初始化
        """
        if cls._pipeline_instance is None:
            raise RuntimeError("模型未初始化，请先调用TextRankingModel.initialize(model_dir)")
        return cls._pipeline_instance(input=inputs)
    
    @classmethod
    def is_initialized(cls):
        """
        检查模型是否已初始化
        
        Returns:
            bool: 是否已初始化
        """
        return cls._pipeline_instance is not None
    
    @classmethod
    def get_model_id(cls):
        """
        获取当前使用的模型ID
        
        Returns:
            str: 模型ID
        """
        return cls._model_id

if __name__=="__main__":
    # 使用示例
    inputs = {
        'source_sentence': ["功和功率的区别"],
        'sentences_to_compare': [
            "功反映做功多少，功率反映做功快慢。",
            "什么是有功功率和无功功率?无功功率有什么用什么是有功功率和无功功率?无功功率有什么用电力系统中的电源是由发电机产生的三相正弦交流电,在交>流电路中,由电源供给负载的电功率有两种;一种是有功功率,一种是无功功率。",
            "优质解答在物理学中,用电功率表示消耗电能的快慢．电功率用P表示,它的单位是瓦特（Watt）,简称瓦（Wa）符号是W.电流在单位时间内做的功叫做电功率 以灯泡为例,电功率越大,灯泡越亮.灯泡的亮暗由电功率（实际功率）决定,不由通过的电流、电压、电能决定!",
        ]
    }

    # 初始化模型
    TextRankingModel.initialize(r"../../model/model_ranking_chinese_tiny")
    
    # 直接使用静态方法进行排序
    result = TextRankingModel.rank(inputs)
    print(result)
    # {'scores': [0.9717444181442261, 0.005540850106626749, 0.8629351258277893]}