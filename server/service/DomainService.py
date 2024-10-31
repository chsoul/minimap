import time

SOCKET_EVENT_DOMAIN_START = 'socket_event_domain_start'
from myutils.configutils import DomainConfig
SOCKET_EVENT_DOMAIN_UPDATE = 'socket_event_domain_update'
SOCKET_EVENT_DOMAIN_END = 'socket_event_domain_end'
SOCKET_EVENT_DOMAIN_EXCEPTION = 'socket_event_domain_exception'
from controller.DomainController import DomainController
from mylogger.MyLogger3 import MyLogger
import threading
logger = MyLogger('domain_service')
class DomainService:
    domain_runner_thread = None
    __lock = threading.Lock()

    @staticmethod
    def get_domain_list():
        return DomainController.get_domain_list()
    
    @staticmethod
    def run_domain(domain_name, fight_team, timeout=None, emit=lambda val1,val2: logger.debug(f'{val1}:{val2}')):
        # socket的emit方法需要在flask运行时赋值，否则就是普通的log方法

        with DomainService.__lock:
            if DomainService.domain_runner_thread is not None:
                if DomainService.domain_runner_thread.is_alive():
                    raise Exception("已经有秘境正在执行中，不要重复执行")

            # 让控制器可以执行
            from controller.BaseController import BaseController
            BaseController.stop_listen = False

            emit(SOCKET_EVENT_DOMAIN_START, f'开始执行{domain_name},队伍为{fight_team}, 时长:{timeout}')
            DomainService.domain_runner_thread = threading.Thread(
                target=DomainController.one_key_run_domain, args=(domain_name, fight_team, timeout,))
            DomainService.domain_runner_thread.start()
        
    @staticmethod
    def stop_domain(emit=lambda val1,val2: logger.debug(f'{val1}:{val2}')):
        from controller.BaseController import BaseController
        BaseController.stop_listen = True
        if DomainService.domain_runner_thread is not None and DomainService.domain_runner_thread.is_alive():
            emit(SOCKET_EVENT_DOMAIN_UPDATE, "等待秘境线程结束")
            DomainService.domain_runner_thread.join()
            emit(SOCKET_EVENT_DOMAIN_END, "秘境线程已结束")
            DomainService.domain_runner_thread = None
        else:
            emit(SOCKET_EVENT_DOMAIN_END, "没有秘境执行，无需停止")
    @staticmethod
    def get_domain_config():
        domain_week_plain = DomainConfig.get(DomainConfig.KEY_DOMAIN_WEEK_PLAIN, default=['','','','','','',''])
        domain_loop_timeout = DomainConfig.get(DomainConfig.KEY_DOMAIN_LOOP_TIMEOUT, default=20)
        domain_team_mapper = DomainConfig.get(DomainConfig.KEY_DOMAIN_TEAM_MAPPER, default=dict())
        data = {
            'domain_week_plain': domain_week_plain,
            'domain_loop_timeout': domain_loop_timeout,
            'domain_team_mapper': domain_team_mapper
        }
        return data

    @staticmethod
    def set_domain_config(data):
        wp = data.get('domain_week_plain',[])
        timeout = data.get('domain_loop_timeout',20)
        domain_team_mapper = data.get('domain_team_mapper', dict())
        if wp is None or timeout is None: raise Exception("秘境配置中存在空值")
        if len(wp) != 7: raise Exception("秘境周计划数组长度必须为7")

        if domain_team_mapper is None: domain_team_mapper = {}

        timeout = int(timeout)
        if timeout < 1: timeout = 1
        if timeout > 600: timeout = 600

        DomainConfig.set(DomainConfig.KEY_DOMAIN_WEEK_PLAIN, wp)
        DomainConfig.set(DomainConfig.KEY_DOMAIN_LOOP_TIMEOUT, timeout)
        DomainConfig.set(DomainConfig.KEY_DOMAIN_TEAM_MAPPER, domain_team_mapper)
        DomainConfig.save_config()


if __name__ == '__main__':
    # name = '虹灵的净土'
    name = '罪祸的终末'
    # fight_team = '纳西妲_芙宁娜_钟离_那维莱特_(草龙芙中).txt'
    # fight_team = '那维莱特_莱依拉_迪希雅_行秋_(龙莱迪行).txt'
    fight_team = '芙宁娜_行秋_莱依拉_流浪者_(芙行莱流).txt'
    # DomainService.run_domain(name, fight_team)
    # time.sleep(10)
    # DomainService.stop_domain()
    conf = DomainService.get_domain_config()
    print(conf)