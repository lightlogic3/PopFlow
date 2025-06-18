import functools
import inspect
def requires_init(func):
    """@Description A decorator that marks methods that need to be initialized first
@Param {function} func - method to decorate
@Returns {function} decorated method"""
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if not self._initialized:
            caller_frame = inspect.currentframe().f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            raise RuntimeError(
                f"错误：在调用 '{func.__name__}' 前，必须先调用 'await init_data()'！"
                f"\n调用位置: {caller_info}"
            )
        return await func(self, *args, **kwargs)
    return wrapper
