#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EcoPort 智慧永續港 - 動態警示版本
綠色港口與永續發展智慧決策平台
包含動態智慧警示系統
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import random
from datetime import datetime, timedelta
import json
import urllib3
import ssl
import os
import numpy as np
import pandas as pd


# 停用SSL警告和驗證
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# 頁面配置
st.set_page_config(
    page_title="EcoPort 智慧永續港",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置類
class Config:
    """應用程式配置"""
    APP_TITLE = "EcoPort 智慧永續港"
    APP_ICON = "🚢"
    
    # API 配置 - 從環境變數或Streamlit secrets讀取
    @property
    def MOENV_API_KEY(self):
        try:
            return st.secrets.get("MOENV_API_KEY", os.getenv("MOENV_API_KEY", ""))
        except:
            return os.getenv("MOENV_API_KEY", "")
    
    @property
    def IMARINE_API_KEY(self):
        try:
            return st.secrets.get("IMARINE_API_KEY", os.getenv("IMARINE_API_KEY", ""))
        except:
            return os.getenv("IMARINE_API_KEY", "")
    
    MOENV_BASE_URL = "https://data.moenv.gov.tw/api/v2"
    IMARINE_BASE_URL = "https://imarine.motcmpb.gov.tw/api"
    
    # API 端點配置
    MOENV_ENDPOINTS = {
        'aqi': 'aqx_p_432',
        'water_quality': 'wqx_p_701',
        'emissions': 'emx_p_301'
    }
    
    IMARINE_ENDPOINTS = {
        'container_import': '/member/data/container/i',
        'container_export': '/member/data/container/e',
        'container_transit': '/member/data/container/t'
    }
    
    # 排放係數配置
    EMISSION_FACTORS = {
        'diesel': 2.68,
        'heavy_oil': 3.15,
        'natural_gas': 2.75,
        'electricity': 0.502
    }
    
    # 警示閾值配置
    ALERT_THRESHOLDS = {
        'carbon_emission_high': 1200,  # 碳排放過高閾值
        'carbon_emission_critical': 1500,  # 碳排放嚴重閾值
        'energy_efficiency_low': 70,  # 能源效率過低閾值
        'energy_consumption_spike': 1.3,  # 能耗異常倍數
        'vessel_congestion': 250,  # 船舶擁塞閾值
        'esg_score_low': 60,  # ESG評分過低閾值
        'renewable_ratio_low': 15,  # 再生能源比例過低閾值
    }

# 實例化配置
config = Config()

# 動態資料生成器（模擬即時數據）
class DynamicDataGenerator:
    """動態資料生成器，模擬即時港口數據"""
    
    def __init__(self):
        self.base_time = datetime.now()
        self.historical_data = self._initialize_historical_data()
    
    def _initialize_historical_data(self):
        """初始化歷史數據"""
        data = []
        for i in range(24):  # 過去24小時
            timestamp = self.base_time - timedelta(hours=i)
            data.append({
                'timestamp': timestamp,
                'carbon_emission': random.uniform(800, 1300),
                'energy_consumption': random.uniform(500, 2000),
                'energy_efficiency': random.uniform(65, 90),
                'vessel_count': random.randint(50, 300),
                'renewable_ratio': random.uniform(10, 35),
                'esg_score': random.randint(50, 95),
                'terminal_1_power': random.uniform(200, 800),
                'terminal_2_power': random.uniform(150, 600),
                'terminal_3_power': random.uniform(300, 900),
                'weather_wind_speed': random.uniform(5, 25),
                'air_quality_aqi': random.randint(20, 150)
            })
        return sorted(data, key=lambda x: x['timestamp'])
    
    def get_latest_data(self):
        """獲取最新數據點"""
        latest = self.historical_data[-1].copy()
        
        # 添加一些隨機變化來模擬即時更新
        latest.update({
            'timestamp': datetime.now(),
            'carbon_emission': latest['carbon_emission'] * random.uniform(0.95, 1.05),
            'energy_consumption': latest['energy_consumption'] * random.uniform(0.9, 1.1),
            'energy_efficiency': max(0, min(100, latest['energy_efficiency'] + random.uniform(-3, 3))),
            'vessel_count': max(0, latest['vessel_count'] + random.randint(-10, 15)),
            'renewable_ratio': max(0, min(50, latest['renewable_ratio'] + random.uniform(-2, 2))),
            'esg_score': max(0, min(100, latest['esg_score'] + random.randint(-5, 5))),
            'terminal_1_power': latest['terminal_1_power'] * random.uniform(0.8, 1.2),
            'terminal_2_power': latest['terminal_2_power'] * random.uniform(0.8, 1.2),
            'terminal_3_power': latest['terminal_3_power'] * random.uniform(0.8, 1.2),
            'weather_wind_speed': max(0, latest['weather_wind_speed'] + random.uniform(-3, 3)),
            'air_quality_aqi': max(0, min(300, latest['air_quality_aqi'] + random.randint(-20, 20)))
        })
        
        return latest
    
    def get_trend_data(self, hours=6):
        """獲取趨勢數據"""
        return self.historical_data[-hours:]

# 智慧警示引擎
class AlertEngine:
    """智慧警示引擎，動態生成各種警示"""
    
    def __init__(self, data_generator):
        self.data_generator = data_generator
        self.active_alerts = []
        self.alert_history = []
    
    def analyze_and_generate_alerts(self):
        """分析數據並生成警示"""
        current_data = self.data_generator.get_latest_data()
        trend_data = self.data_generator.get_trend_data()
        
        self.active_alerts = []
        
        # 1. 碳排放警示
        self._check_carbon_emission_alerts(current_data, trend_data)
        
        # 2. 能源相關警示
        self._check_energy_alerts(current_data, trend_data)
        
        # 3. 設備異常警示
        self._check_equipment_alerts(current_data, trend_data)
        
        # 4. 環境警示
        self._check_environmental_alerts(current_data)
        
        # 5. 營運警示
        self._check_operational_alerts(current_data, trend_data)
        
        # 6. ESG警示
        self._check_esg_alerts(current_data)
        
        # 7. 預測性警示
        self._check_predictive_alerts(trend_data)
        
        # 更新警示歷史
        self._update_alert_history()
        
        return self.active_alerts
    
    def _check_carbon_emission_alerts(self, current_data, trend_data):
        """檢查碳排放相關警示"""
        emission = current_data['carbon_emission']
        
        if emission > config.ALERT_THRESHOLDS['carbon_emission_critical']:
            self.active_alerts.append({
                'type': 'error',
                'priority': 'critical',
                'title': '🚨 碳排放嚴重超標',
                'message': f'當前碳排放量 {emission:.0f} 噸CO₂/小時，超過嚴重警戒值 {config.ALERT_THRESHOLDS["carbon_emission_critical"]} 噸',
                'recommendation': '立即停止非必要高耗能設備，啟動緊急減排程序',
                'timestamp': current_data['timestamp'],
                'category': 'emission'
            })
        elif emission > config.ALERT_THRESHOLDS['carbon_emission_high']:
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'high',
                'title': '⚠️ 碳排放量偏高',
                'message': f'當前碳排放量 {emission:.0f} 噸CO₂/小時，超過預警值 {config.ALERT_THRESHOLDS["carbon_emission_high"]} 噸',
                'recommendation': '建議優化作業調度，減少同時運行的高排放設備',
                'timestamp': current_data['timestamp'],
                'category': 'emission'
            })
        
        # 檢查排放趨勢
        if len(trend_data) >= 3:
            recent_emissions = [d['carbon_emission'] for d in trend_data[-3:]]
            if all(recent_emissions[i] < recent_emissions[i+1] for i in range(len(recent_emissions)-1)):
                increase_rate = (recent_emissions[-1] - recent_emissions[0]) / recent_emissions[0] * 100
                if increase_rate > 15:
                    self.active_alerts.append({
                        'type': 'warning',
                        'priority': 'medium',
                        'title': '📈 碳排放持續上升',
                        'message': f'過去3小時碳排放量持續上升，增幅達 {increase_rate:.1f}%',
                        'recommendation': '檢查設備運行狀態，考慮調整作業強度',
                        'timestamp': current_data['timestamp'],
                        'category': 'trend'
                    })
    
    def _check_energy_alerts(self, current_data, trend_data):
        """檢查能源相關警示"""
        efficiency = current_data['energy_efficiency']
        consumption = current_data['energy_consumption']
        renewable = current_data['renewable_ratio']
        
        # 能源效率警示
        if efficiency < config.ALERT_THRESHOLDS['energy_efficiency_low']:
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'medium',
                'title': '⚡ 能源效率偏低',
                'message': f'當前能源效率 {efficiency:.1f}%，低於標準值 {config.ALERT_THRESHOLDS["energy_efficiency_low"]}%',
                'recommendation': '檢查設備運行狀態，進行維護保養以提升效率',
                'timestamp': current_data['timestamp'],
                'category': 'efficiency'
            })
        
        # 能耗異常警示
        if len(trend_data) >= 2:
            avg_consumption = np.mean([d['energy_consumption'] for d in trend_data[:-1]])
            if consumption > avg_consumption * config.ALERT_THRESHOLDS['energy_consumption_spike']:
                self.active_alerts.append({
                    'type': 'error',
                    'priority': 'high',
                    'title': '⚡ 能耗異常飆升',
                    'message': f'當前能耗 {consumption:.0f} kW，比平均值高出 {((consumption/avg_consumption-1)*100):.0f}%',
                    'recommendation': '立即檢查所有設備運行狀態，查找異常耗能設備',
                    'timestamp': current_data['timestamp'],
                    'category': 'consumption'
                })
        
        # 再生能源比例警示
        if renewable < config.ALERT_THRESHOLDS['renewable_ratio_low']:
            self.active_alerts.append({
                'type': 'info',
                'priority': 'low',
                'title': '🔋 再生能源使用不足',
                'message': f'再生能源使用比例僅 {renewable:.1f}%，建議提升至 {config.ALERT_THRESHOLDS["renewable_ratio_low"]}% 以上',
                'recommendation': '增加太陽能、風能等再生能源的使用',
                'timestamp': current_data['timestamp'],
                'category': 'renewable'
            })
    
    def _check_equipment_alerts(self, current_data, trend_data):
        """檢查設備異常警示"""
        terminals = {
            '第1號碼頭': current_data['terminal_1_power'],
            '第2號碼頭': current_data['terminal_2_power'],
            '第3號碼頭': current_data['terminal_3_power']
        }
        
        for terminal, power in terminals.items():
            if power > 700:  # 高功率警示
                self.active_alerts.append({
                    'type': 'warning',
                    'priority': 'medium',
                    'title': f'🏭 {terminal}功率異常',
                    'message': f'{terminal}當前功率 {power:.0f} kW，超過正常運行範圍',
                    'recommendation': f'檢查{terminal}設備狀態，確認是否有設備故障',
                    'timestamp': current_data['timestamp'],
                    'category': 'equipment'
                })
            elif power < 100:  # 低功率警示（可能設備停機）
                self.active_alerts.append({
                    'type': 'info',
                    'priority': 'low',
                    'title': f'🔧 {terminal}功率過低',
                    'message': f'{terminal}當前功率僅 {power:.0f} kW，設備可能未充分利用',
                    'recommendation': f'確認{terminal}作業計畫，檢查是否需要增加設備運行',
                    'timestamp': current_data['timestamp'],
                    'category': 'equipment'
                })
    
    def _check_environmental_alerts(self, current_data):
        """檢查環境相關警示"""
        wind_speed = current_data['weather_wind_speed']
        aqi = current_data['air_quality_aqi']
        
        # 天氣警示
        if wind_speed > 20:
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'medium',
                'title': '🌪️ 強風天氣警示',
                'message': f'當前風速 {wind_speed:.1f} m/s，可能影響貨櫃作業安全',
                'recommendation': '加強貨櫃固定，暫停高空作業，注意人員安全',
                'timestamp': current_data['timestamp'],
                'category': 'weather'
            })
        
        # 空氣品質警示
        if aqi > 100:
            level = "不健康" if aqi > 150 else "對敏感族群不健康"
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'medium',
                'title': '🌫️ 空氣品質警示',
                'message': f'當前AQI指數 {aqi}，空氣品質{level}',
                'recommendation': '建議戶外作業人員配戴防護口罩，減少不必要的戶外活動',
                'timestamp': current_data['timestamp'],
                'category': 'environment'
            })
    
    def _check_operational_alerts(self, current_data, trend_data):
        """檢查營運相關警示"""
        vessel_count = current_data['vessel_count']
        
        # 船舶擁塞警示
        if vessel_count > config.ALERT_THRESHOLDS['vessel_congestion']:
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'high',
                'title': '🚢 港口船舶擁塞',
                'message': f'當前在港船舶 {vessel_count} 艘，超過港口最佳容量',
                'recommendation': '優化船舶調度，加快裝卸作業效率，考慮延後部分船舶進港',
                'timestamp': current_data['timestamp'],
                'category': 'operation'
            })
        
        # 檢查船舶數量趨勢
        if len(trend_data) >= 4:
            recent_vessels = [d['vessel_count'] for d in trend_data[-4:]]
            if all(recent_vessels[i] < recent_vessels[i+1] for i in range(len(recent_vessels)-1)):
                self.active_alerts.append({
                    'type': 'info',
                    'priority': 'medium',
                    'title': '📈 船舶數量持續增加',
                    'message': f'過去4小時船舶數量持續增加，當前 {vessel_count} 艘',
                    'recommendation': '準備增加作業人力和設備，預防港口擁塞',
                    'timestamp': current_data['timestamp'],
                    'category': 'trend'
                })
    
    def _check_esg_alerts(self, current_data):
        """檢查ESG相關警示"""
        esg_score = current_data['esg_score']
        
        if esg_score < config.ALERT_THRESHOLDS['esg_score_low']:
            self.active_alerts.append({
                'type': 'warning',
                'priority': 'medium',
                'title': '📊 ESG評分偏低',
                'message': f'當前ESG評分 {esg_score} 分，低於目標值 {config.ALERT_THRESHOLDS["esg_score_low"]} 分',
                'recommendation': '加強環境保護措施，提升社會責任表現，改善治理結構',
                'timestamp': current_data['timestamp'],
                'category': 'esg'
            })
    
    def _check_predictive_alerts(self, trend_data):
        """檢查預測性警示"""
        if len(trend_data) >= 6:
            # 預測未來2小時的碳排放趨勢
            emissions = [d['carbon_emission'] for d in trend_data]
            
            # 簡單線性趨勢預測
            x = np.arange(len(emissions))
            coefficients = np.polyfit(x, emissions, 1)
            
            # 預測未來2小時
            future_emission = coefficients[0] * (len(emissions) + 2) + coefficients[1]
            
            if future_emission > config.ALERT_THRESHOLDS['carbon_emission_high']:
                self.active_alerts.append({
                    'type': 'info',
                    'priority': 'medium',
                    'title': '🔮 預測性警示',
                    'message': f'根據趨勢分析，預計2小時後碳排放可能達到 {future_emission:.0f} 噸CO₂/小時',
                    'recommendation': '建議提前調整作業計畫，避免排放峰值',
                    'timestamp': datetime.now(),
                    'category': 'prediction'
                })
    
    def _update_alert_history(self):
        """更新警示歷史"""
        for alert in self.active_alerts:
            self.alert_history.append(alert)
        
        # 保留最近50條歷史記錄
        if len(self.alert_history) > 50:
            self.alert_history = self.alert_history[-50:]
    
    def get_alert_statistics(self):
        """獲取警示統計資訊"""
        if not self.alert_history:
            return {}
        
        total = len(self.alert_history)
        by_type = {}
        by_category = {}
        by_priority = {}
        
        for alert in self.alert_history:
            # 按類型統計
            alert_type = alert['type']
            by_type[alert_type] = by_type.get(alert_type, 0) + 1
            
            # 按分類統計
            category = alert['category']
            by_category[category] = by_category.get(category, 0) + 1
            
            # 按優先級統計
            priority = alert['priority']
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        return {
            'total': total,
            'by_type': by_type,
            'by_category': by_category,
            'by_priority': by_priority
        }

# API 服務類（保持原有功能）
class APIService:
    """API服務類，處理所有外部API呼叫"""
    
    @staticmethod
    def fetch_moenv_data(endpoint, params=None):
        """調用環境部API"""
        if not config.MOENV_API_KEY:
            st.warning("⚠️ 環境部API密鑰未設定")
            return None
            
        if params is None:
            params = {}
        
        params.update({
            'api_key': config.MOENV_API_KEY,
            'format': 'json',
            'limit': 1000,
            'offset': 0
        })
        
        try:
            url = f"{config.MOENV_BASE_URL}/{endpoint}"
            st.write(f"🔄 正在調用環境部API...")
            
            response = requests.get(url, params=params, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            st.success(f"✅ 環境部API調用成功")
            return data
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ 環境部API調用失敗")
            return None
    
    @staticmethod
    def fetch_imarine_data(endpoint, params=None):
        """調用iMarine API"""
        if not config.IMARINE_API_KEY:
            st.warning("⚠️ iMarine API密鑰未設定")
            return None
            
        try:
            url = f"{config.IMARINE_BASE_URL}{endpoint}"
            
            headers = {
                'Authorization': config.IMARINE_API_KEY,
                'Content-Type': 'application/json'
            }
            
            post_data = {
                "Start": "202301",
                "End": "202505", 
                "IPortLevel": 1,
                "IPort": [
                    "USLAX", "CNSHA", "HKHKG", "SGSIN", "THLCH", 
                    "KRPUS", "CNXMN", "MYPKG", "JPYOK", "JPTYO"
                ]
            }
            
            st.write(f"🔄 正在調用iMarine API...")
            
            response = requests.post(url, json=post_data, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            data = response.json()
            st.success(f"✅ iMarine API調用成功")
            return data
            
        except requests.exceptions.RequestException as e:
            st.error(f"❌ iMarine API調用失敗")
            return None
    
    @staticmethod
    def get_air_quality_data():
        """取得空氣品質資料"""
        return APIService.fetch_moenv_data(config.MOENV_ENDPOINTS['aqi'])
    
    @staticmethod
    def get_water_quality_data():
        """取得水質資料"""
        return APIService.fetch_moenv_data(config.MOENV_ENDPOINTS['water_quality'])
    
    @staticmethod
    def get_port_data():
        """取得港口貨櫃資料"""
        return APIService.fetch_imarine_data(config.IMARINE_ENDPOINTS['container_import'])

# 碳排放計算引擎（保持原有功能）
class CarbonCalculator:
    """碳排放計算引擎"""
    
    @staticmethod
    def calculate_ship_emissions(fuel_type, operation_hours, fuel_consumption):
        """計算船舶碳排放"""
        factor = config.EMISSION_FACTORS.get(fuel_type, config.EMISSION_FACTORS['diesel'])
        emission = (fuel_consumption * operation_hours * factor) / 1000
        return round(emission, 2)
    
    @staticmethod
    def calculate_port_equipment_emissions(power_consumption, operation_hours):
        """計算港口設備碳排放"""
        factor = config.EMISSION_FACTORS['electricity']
        emission = (power_consumption * operation_hours * factor) / 1000
        return round(emission, 2)
    
    @staticmethod
    def calculate_esg_score(carbon_emission, energy_efficiency, renewable_ratio):
        """計算ESG評分"""
        carbon_score = max(0, 100 - (carbon_emission / 10))
        total_score = (
            carbon_score * 0.4 +
            energy_efficiency * 0.3 +
            renewable_ratio * 0.3
        )
        return round(min(100, max(0, total_score)))

# 靜態資料生成器（保持原有功能）
class DataGenerator:
    """靜態資料生成器"""
    
    @staticmethod
    def generate_carbon_trend_data():
        """生成碳排放趨勢資料"""
        months = ['1月', '2月', '3月', '4月', '5月', '6月']
        data = []
        
        for i, month in enumerate(months):
            base_emission = 1000
            seasonal_factor = 1 + 0.1 * (i / 6)
            random_factor = random.uniform(0.9, 1.1)
            
            emission = base_emission * seasonal_factor * random_factor
            efficiency = random.uniform(80, 90)
            renewable = random.uniform(20, 30)
            
            data.append({
                'month': month,
                'emission': round(emission, 2),
                'target': 1000,
                'efficiency': round(efficiency, 1),
                'renewable_ratio': round(renewable, 1)
            })
        
        return data
    
    @staticmethod
    def generate_port_comparison_data():
        """生成港口比較資料"""
        ports_info = {
            '高雄港': {'base_emission': 1200, 'efficiency_range': (82, 88), 'vessels': (200, 300)},
            '基隆港': {'base_emission': 800, 'efficiency_range': (75, 82), 'vessels': (120, 180)},
            '台中港': {'base_emission': 600, 'efficiency_range': (78, 85), 'vessels': (80, 120)},
            '花蓮港': {'base_emission': 300, 'efficiency_range': (70, 78), 'vessels': (30, 60)}
        }
        
        data = []
        for port, info in ports_info.items():
            emission_variation = random.uniform(0.85, 1.15)
            efficiency = random.uniform(*info['efficiency_range'])
            vessels = random.randint(*info['vessels'])
            
            data.append({
                'port': port,
                'carbon_emission': round(info['base_emission'] * emission_variation, 2),
                'efficiency': round(efficiency, 1),
                'vessels_count': vessels,
                'energy_consumption': round(random.uniform(500, 2000), 2),
                'esg_score': CarbonCalculator.calculate_esg_score(
                    info['base_emission'] * emission_variation, 
                    efficiency, 
                    random.uniform(20, 30)
                )
            })
        
        return data

# 視覺化工具（保持原有功能）
class Visualizer:
    """圖表視覺化工具"""
    
    @staticmethod
    def create_carbon_trend_chart(data):
        """建立碳排放趨勢圖"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('碳排放趨勢', '能源效率趨勢'),
            specs=[[{"secondary_y": True}, {"secondary_y": False}]]
        )
        
        months = [d['month'] for d in data]
        emissions = [d['emission'] for d in data]
        targets = [d['target'] for d in data]
        efficiency = [d['efficiency'] for d in data]
        
        # 碳排放趨勢
        fig.add_trace(
            go.Scatter(x=months, y=emissions, mode='lines+markers', 
                      name='實際排放', line=dict(color='red', width=3)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=months, y=targets, mode='lines+markers', 
                      name='目標排放', line=dict(color='green', width=3, dash='dash')),
            row=1, col=1
        )
        
        # 能源效率趨勢
        fig.add_trace(
            go.Scatter(x=months, y=efficiency, mode='lines+markers', 
                      name='能源效率', line=dict(color='blue', width=3)),
            row=1, col=2
        )
        
        fig.update_layout(height=400, title_text="碳排與能源視覺儀表板")
        return fig
    
    @staticmethod
    def create_port_comparison_chart(data):
        """建立港口比較圖"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('碳排放比較', '能源效率比較', 'ESG評分比較', '船舶數量比較'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        ports = [d['port'] for d in data]
        
        # 碳排放
        fig.add_trace(
            go.Bar(x=ports, y=[d['carbon_emission'] for d in data], 
                   name='碳排放', marker_color='red'),
            row=1, col=1
        )
        
        # 能源效率
        fig.add_trace(
            go.Bar(x=ports, y=[d['efficiency'] for d in data], 
                   name='能源效率', marker_color='green'),
            row=1, col=2
        )
        
        # ESG評分
        fig.add_trace(
            go.Bar(x=ports, y=[d['esg_score'] for d in data], 
                   name='ESG評分', marker_color='blue'),
            row=2, col=1
        )
        
        # 船舶數量
        fig.add_trace(
            go.Bar(x=ports, y=[d['vessels_count'] for d in data], 
                   name='船舶數量', marker_color='orange'),
            row=2, col=2
        )
        
        fig.update_layout(height=600, title_text="港口永續績效比較", showlegend=False)
        return fig
    
    @staticmethod
    def create_realtime_monitoring_chart(trend_data):
        """建立即時監控圖表"""
        if not trend_data:
            return go.Figure()
        
        timestamps = [d['timestamp'].strftime('%H:%M') for d in trend_data]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('碳排放即時監控', '能源消耗即時監控', '船舶數量變化', '能源效率變化'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 碳排放
        fig.add_trace(
            go.Scatter(x=timestamps, y=[d['carbon_emission'] for d in trend_data],
                      mode='lines+markers', name='碳排放', line=dict(color='red')),
            row=1, col=1
        )
        
        # 能源消耗
        fig.add_trace(
            go.Scatter(x=timestamps, y=[d['energy_consumption'] for d in trend_data],
                      mode='lines+markers', name='能源消耗', line=dict(color='orange')),
            row=1, col=2
        )
        
        # 船舶數量
        fig.add_trace(
            go.Scatter(x=timestamps, y=[d['vessel_count'] for d in trend_data],
                      mode='lines+markers', name='船舶數量', line=dict(color='blue')),
            row=2, col=1
        )
        
        # 能源效率
        fig.add_trace(
            go.Scatter(x=timestamps, y=[d['energy_efficiency'] for d in trend_data],
                      mode='lines+markers', name='能源效率', line=dict(color='green')),
            row=2, col=2
        )
        
        fig.update_layout(height=500, title_text="即時監控儀表板", showlegend=False)
        return fig

# 主應用程式
def main():
    """主應用程式"""
    
    # 初始化會話狀態
    if 'api_test_results' not in st.session_state:
        st.session_state.api_test_results = {}
    
    if 'data_generator' not in st.session_state:
        st.session_state.data_generator = DynamicDataGenerator()
    
    if 'alert_engine' not in st.session_state:
        st.session_state.alert_engine = AlertEngine(st.session_state.data_generator)
    
    # 主標題
    st.title(f"{config.APP_ICON} {config.APP_TITLE}")
    st.markdown("### 綠色港口與永續發展智慧決策平台")
    st.markdown("**主題對應：綠色港口發展應用、航運產業脫碳策略應用、永續發展政策創新**")
    
    # 側邊欄
    with st.sidebar:
        st.header("📊 控制面板")
        
        # 即時更新按鈕
        if st.button("🔄 更新即時數據", use_container_width=True):
            st.session_state.data_generator = DynamicDataGenerator()
            st.session_state.alert_engine = AlertEngine(st.session_state.data_generator)
            st.rerun()
        
        # API連接狀態顯示
        st.subheader("🔌 API 連接狀態")
        
        # 檢查API密鑰是否設定
        moenv_status = "✅ 已設定" if config.MOENV_API_KEY else "❌ 未設定"
        imarine_status = "✅ 已設定" if config.IMARINE_API_KEY else "❌ 未設定"
        
        st.write(f"🌍 環境部API: {moenv_status}")
        st.write(f"🚢 iMarine API: {imarine_status}")
        
        # 警示設定
        st.subheader("⚙️ 警示設定")
        
        # 動態調整警示閾值
        with st.expander("調整警示閾值"):
            config.ALERT_THRESHOLDS['carbon_emission_high'] = st.slider(
                "碳排放警戒值 (噸CO₂/小時)", 
                800, 2000, 
                config.ALERT_THRESHOLDS['carbon_emission_high']
            )
            
            config.ALERT_THRESHOLDS['energy_efficiency_low'] = st.slider(
                "能源效率警戒值 (%)", 
                50, 90, 
                config.ALERT_THRESHOLDS['energy_efficiency_low']
            )
            
            config.ALERT_THRESHOLDS['vessel_congestion'] = st.slider(
                "船舶擁塞警戒值 (艘)", 
                100, 400, 
                config.ALERT_THRESHOLDS['vessel_congestion']
            )
        
        st.divider()
        
        # 資料篩選
        st.subheader("📅 資料篩選")
        selected_ports = st.multiselect(
            "選擇港口",
            ["高雄港", "基隆港", "台中港", "花蓮港"],
            default=["高雄港", "基隆港"]
        )
        
        date_range = st.date_input(
            "資料時間範圍",
            value=[datetime.now() - timedelta(days=30), datetime.now()]
        )
    
    # 主要內容區域
    tabs = st.tabs([
        "📊 總覽儀表板", 
        "🌱 碳排放監控", 
        "⚡ 能源管理", 
        "🏭 港口比較", 
        "🚨 智慧警示",
        "📈 即時監控"
    ])
    
    # 總覽儀表板
    with tabs[0]:
        st.header("📊 碳排與能源視覺儀表板")
        st.markdown("**展示港口碳排趨勢、能源使用結構、目標達成率**")
        
        # 獲取最新數據
        current_data = st.session_state.data_generator.get_latest_data()
        
        # 核心指標
        st.subheader("📈 核心永續指標")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌱 當前碳排放", f"{current_data['carbon_emission']:.0f} 噸 CO₂/小時", f"{random.uniform(-10, 10):.1f}%")
        with col2:
            st.metric("📈 ESG 評分", f"{current_data['esg_score']} 分", f"{random.uniform(-5, 5):.1f}%")
        with col3:
            st.metric("⚡ 能源效率", f"{current_data['energy_efficiency']:.1f}%", f"{random.uniform(-3, 3):.1f}%")
        with col4:
            st.metric("🔋 再生能源佔比", f"{current_data['renewable_ratio']:.1f}%", f"{random.uniform(0, 8):.1f}%")
        
        # 趨勢圖表
        st.subheader("📊 趨勢分析 (年/月/即時視角)")
        carbon_data = DataGenerator.generate_carbon_trend_data()
        trend_chart = Visualizer.create_carbon_trend_chart(carbon_data)
        st.plotly_chart(trend_chart, use_container_width=True)
        
        # 能源結構分析
        st.subheader("⚡ 能源使用結構分析")
        energy_data = [45, 30, 20, 5]
        energy_labels = ['電力', '柴油', '重油', '天然氣']
        
        fig = px.pie(values=energy_data, names=energy_labels, 
                    title="港口能源使用結構",
                    color_discrete_sequence=['#3B82F6', '#EF4444', '#F59E0B', '#10B981'])
        st.plotly_chart(fig, use_container_width=True)
    
    # 碳排放監控
    with tabs[1]:
        st.header("🌱 碳排放監控與計算")
        st.markdown("**碳排估算與趨勢預測 (依據燃料類型與作業時長)**")
        
        # 碳排放計算器
        st.subheader("🧮 碳排放計算引擎")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🚢 船舶靠港排放估算**")
            fuel_type = st.selectbox(
                "燃料類型",
                options=["diesel", "heavy_oil", "natural_gas"],
                format_func=lambda x: {"diesel": "柴油", "heavy_oil": "重油", "natural_gas": "天然氣"}[x]
            )
            operation_hours = st.number_input("作業時間 (小時)", min_value=0.0, value=8.0, step=0.5)
            fuel_consumption = st.number_input("燃料消耗 (公升/小時)", min_value=0.0, value=100.0, step=5.0)
            
            if st.button("計算船舶排放", use_container_width=True):
                emission = CarbonCalculator.calculate_ship_emissions(fuel_type, operation_hours, fuel_consumption)
                st.success(f"⚡ 預估碳排放: **{emission} 噸 CO₂**")
                
                # 顯示計算過程
                factor = config.EMISSION_FACTORS[fuel_type]
                st.info(f"💡 計算過程: {fuel_consumption} L/h × {operation_hours} h × {factor} kg CO₂/L ÷ 1000 = {emission} 噸 CO₂")
        
        with col2:
            st.markdown("**🏭 港口設備排放計算**")
            power_consumption = st.number_input("功率消耗 (kW)", min_value=0.0, value=500.0, step=10.0)
            equipment_hours = st.number_input("設備運行時間 (小時)", min_value=0.0, value=10.0, step=0.5)
            
            if st.button("計算設備排放", use_container_width=True):
                emission = CarbonCalculator.calculate_port_equipment_emissions(power_consumption, equipment_hours)
                st.success(f"⚡ 預估碳排放: **{emission} 噸 CO₂**")
                
                # 顯示計算過程
                factor = config.EMISSION_FACTORS['electricity']
                st.info(f"💡 計算過程: {power_consumption} kW × {equipment_hours} h × {factor} kg CO₂/kWh ÷ 1000 = {emission} 噸 CO₂")
        
        # AI 模型預測
        st.subheader("🤖 AI 模型預測未來排放趨勢")
        if st.button("🔮 預測未來3個月排放趨勢"):
            st.info("🔄 AI模型分析中...")
            
            # 基於當前趨勢進行預測
            trend_data = st.session_state.data_generator.get_trend_data(6)
            recent_emissions = [d['carbon_emission'] for d in trend_data]
            
            future_months = ['7月', '8月', '9月']
            predictions = []
            
            # 簡單趨勢預測
            avg_change = np.mean(np.diff(recent_emissions)) if len(recent_emissions) > 1 else 0
            base_emission = recent_emissions[-1] if recent_emissions else 1000
            
            for i, month in enumerate(future_months):
                pred_emission = base_emission + avg_change * (i + 1) + random.uniform(-50, 50)
                predictions.append({'month': month, 'predicted_emission': max(0, pred_emission)})
            
            st.success("✅ 預測完成！")
            for pred in predictions:
                st.write(f"📅 {pred['month']}: 預測排放 {pred['predicted_emission']:.0f} 噸 CO₂")
    
    # 能源管理
    with tabs[2]:
        st.header("⚡ 能源管理與效率分析")
        
        # 即時能源數據
        current_data = st.session_state.data_generator.get_latest_data()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            energy_data = [45, 30, 20, 5]
            energy_labels = ['電力', '柴油', '重油', '天然氣']
            fig = px.pie(values=energy_data, names=energy_labels, hole=0.3,
                        title="港口能源使用結構")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("即時能源指標")
            st.metric("能源效率", f"{current_data['energy_efficiency']:.1f}%")
            st.metric("總能耗", f"{current_data['energy_consumption']:.0f} kW")
            st.metric("再生能源比例", f"{current_data['renewable_ratio']:.1f}%")
        
        # 各碼頭能耗監控
        st.subheader("🏭 各碼頭即時能耗監控")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            terminal_1_power = current_data['terminal_1_power']
            status_1 = "⚠️ 異常" if terminal_1_power > 700 or terminal_1_power < 100 else "✅ 正常"
            st.metric("第1號碼頭", f"{terminal_1_power:.0f} kW", help=f"狀態: {status_1}")
        
        with col2:
            terminal_2_power = current_data['terminal_2_power']
            status_2 = "⚠️ 異常" if terminal_2_power > 700 or terminal_2_power < 100 else "✅ 正常"
            st.metric("第2號碼頭", f"{terminal_2_power:.0f} kW", help=f"狀態: {status_2}")
        
        with col3:
            terminal_3_power = current_data['terminal_3_power']
            status_3 = "⚠️ 異常" if terminal_3_power > 700 or terminal_3_power < 100 else "✅ 正常"
            st.metric("第3號碼頭", f"{terminal_3_power:.0f} kW", help=f"狀態: {status_3}")
        
        # 智慧節能建議
        st.subheader("💡 智慧節能建議")
        recommendations = [
            "🔋 建議將再生能源使用比例提升至30%以上",
            "⏰ 優化港口設備運行時間，避免尖峰時段高耗能作業", 
            "🚛 考慮引入電動港口設備，減少柴油使用",
            "🔌 建立智慧電網系統，提高能源使用效率"
        ]
        
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # 港口比較
    with tabs[3]:
        st.header("🏭 港口永續績效比較")
        st.markdown("**多港口ESG表現對比分析**")
        
        port_data = DataGenerator.generate_port_comparison_data()
        
        # 港口比較圖表
        comparison_chart = Visualizer.create_port_comparison_chart(port_data)
        st.plotly_chart(comparison_chart, use_container_width=True)
        
        # 詳細資料表
        st.subheader("📋 港口詳細績效資料")
        
        # 建立表格顯示
        for port in port_data:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.write(f"**{port['port']}**")
            with col2:
                st.metric("碳排放", f"{port['carbon_emission']:.0f} 噸")
            with col3:
                st.metric("效率", f"{port['efficiency']:.1f}%")
            with col4:
                st.metric("船舶數", f"{port['vessels_count']}")
            with col5:
                st.metric("ESG評分", f"{port['esg_score']}")
    
    # 智慧警示（動態版本）
    with tabs[4]:
        st.header("🚨 智慧警示與節能建議")
        st.markdown("**自動偵測高耗能或異常排放事件 - 動態分析系統**")
        
        # 生成動態警示
        active_alerts = st.session_state.alert_engine.analyze_and_generate_alerts()
        
        # 警示統計
        alert_stats = st.session_state.alert_engine.get_alert_statistics()
        
        if alert_stats:
            st.subheader("📊 警示統計總覽")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("總警示數", alert_stats['total'])
            with col2:
                critical_count = alert_stats['by_priority'].get('critical', 0)
                st.metric("緊急警示", critical_count)
            with col3:
                high_count = alert_stats['by_priority'].get('high', 0)
                st.metric("高優先級", high_count)
            with col4:
                medium_count = alert_stats['by_priority'].get('medium', 0)
                st.metric("中優先級", medium_count)
        
        # 當前活躍警示
        st.subheader("⚡ 當前活躍警示")
        
        if not active_alerts:
            st.success("✅ 目前所有系統運行正常，無活躍警示")
        else:
            # 按優先級排序警示
            priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
            sorted_alerts = sorted(active_alerts, key=lambda x: priority_order.get(x['priority'], 4))
            
            for alert in sorted_alerts:
                if alert['type'] == 'error':
                    with st.container():
                        st.error(f"""
                        **{alert['title']}**
                        
                        {alert['message']}
                        
                        **💡 建議措施:** {alert['recommendation']}
                        
                        *時間: {alert['timestamp'].strftime('%H:%M:%S')} | 分類: {alert['category']} | 優先級: {alert['priority']}*
                        """)
                elif alert['type'] == 'warning':
                    with st.container():
                        st.warning(f"""
                        **{alert['title']}**
                        
                        {alert['message']}
                        
                        **💡 建議措施:** {alert['recommendation']}
                        
                        *時間: {alert['timestamp'].strftime('%H:%M:%S')} | 分類: {alert['category']} | 優先級: {alert['priority']}*
                        """)
                elif alert['type'] == 'info':
                    with st.container():
                        st.info(f"""
                        **{alert['title']}**
                        
                        {alert['message']}
                        
                        **💡 建議措施:** {alert['recommendation']}
                        
                        *時間: {alert['timestamp'].strftime('%H:%M:%S')} | 分類: {alert['category']} | 優先級: {alert['priority']}*
                        """)
                else:
                    with st.container():
                        st.success(f"""
                        **{alert['title']}**
                        
                        {alert['message']}
                        
                        **💡 建議措施:** {alert['recommendation']}
                        
                        *時間: {alert['timestamp'].strftime('%H:%M:%S')} | 分類: {alert['category']} | 優先級: {alert['priority']}*
                        """)
        
        # 警示分類統計
        if alert_stats and alert_stats['by_category']:
            st.subheader("📈 警示分類統計")
            
            categories = list(alert_stats['by_category'].keys())
            counts = list(alert_stats['by_category'].values())
            
            fig = px.bar(x=categories, y=counts, 
                        title="各類別警示數量統計",
                        labels={'x': '警示類別', 'y': '數量'})
            st.plotly_chart(fig, use_container_width=True)
        
        # 預防性維護建議
        st.subheader("🔧 預防性維護建議")
        
        current_data = st.session_state.data_generator.get_latest_data()
        
        maintenance_suggestions = []
        
        if current_data['energy_efficiency'] < 80:
            maintenance_suggestions.append("🔧 建議對港口主要設備進行效能檢查和維護")
        
        if current_data['terminal_1_power'] > 600 or current_data['terminal_2_power'] > 600 or current_data['terminal_3_power'] > 600:
            maintenance_suggestions.append("⚡ 高功耗碼頭設備需要進行電氣系統檢查")
        
        if current_data['renewable_ratio'] < 20:
            maintenance_suggestions.append("🌱 檢查再生能源設備運行狀態，提升綠色能源使用率")
        
        maintenance_suggestions.extend([
            "📅 建議每週定期檢查港機設備潤滑狀態",
            "🔍 每月進行能源計量設備校準",
            "🌡️ 定期監控設備運行溫度，預防過熱",
            "📊 建立設備運行數據基線，便於異常檢測"
        ])
        
        for suggestion in maintenance_suggestions:
            st.write(f"• {suggestion}")
    
    # 即時監控
    with tabs[5]:
        st.header("📈 即時監控中心")
        st.markdown("**港口營運即時數據監控與分析**")
        
        # 即時數據更新
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🔄 重新整理數據", use_container_width=True):
                st.rerun()
            
            st.metric("數據更新時間", datetime.now().strftime('%H:%M:%S'))
        
        with col1:
            st.markdown("**系統會自動監控港口各項營運指標，及時發現異常狀況**")
        
        # 即時監控圖表
        trend_data = st.session_state.data_generator.get_trend_data(12)  # 過去12小時
        
        if trend_data:
            monitoring_chart = Visualizer.create_realtime_monitoring_chart(trend_data)
            st.plotly_chart(monitoring_chart, use_container_width=True)
        
        # 關鍵指標監控
        st.subheader("🎯 關鍵指標即時監控")
        
        current_data = st.session_state.data_generator.get_latest_data()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            carbon_color = "normal"
            if current_data['carbon_emission'] > config.ALERT_THRESHOLDS['carbon_emission_critical']:
                carbon_color = "off"
            elif current_data['carbon_emission'] > config.ALERT_THRESHOLDS['carbon_emission_high']:
                carbon_color = "inverse"
                
            st.metric("碳排放", f"{current_data['carbon_emission']:.0f}", 
                     help="噸CO₂/小時")
        
        with col2:
            efficiency_color = "inverse" if current_data['energy_efficiency'] < config.ALERT_THRESHOLDS['energy_efficiency_low'] else "normal"
            st.metric("能源效率", f"{current_data['energy_efficiency']:.1f}%")
        
        with col3:
            vessel_color = "inverse" if current_data['vessel_count'] > config.ALERT_THRESHOLDS['vessel_congestion'] else "normal"
            st.metric("在港船舶", f"{current_data['vessel_count']}")
        
        with col4:
            st.metric("總能耗", f"{current_data['energy_consumption']:.0f} kW")
        
        with col5:
            renewable_color = "inverse" if current_data['renewable_ratio'] < config.ALERT_THRESHOLDS['renewable_ratio_low'] else "normal"
            st.metric("再生能源", f"{current_data['renewable_ratio']:.1f}%")
        
        with col6:
            esg_color = "inverse" if current_data['esg_score'] < config.ALERT_THRESHOLDS['esg_score_low'] else "normal"
            st.metric("ESG評分", f"{current_data['esg_score']}")
        
        # 環境監控
        st.subheader("🌍 環境監控")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            wind_status = "⚠️ 強風" if current_data['weather_wind_speed'] > 20 else "✅ 正常"
            st.metric("風速", f"{current_data['weather_wind_speed']:.1f} m/s", help=f"狀態: {wind_status}")
        
        with col2:
            aqi_status = "⚠️ 不良" if current_data['air_quality_aqi'] > 100 else "✅ 良好"
            st.metric("空氣品質 AQI", f"{current_data['air_quality_aqi']}", help=f"狀態: {aqi_status}")
        
        with col3:
            st.metric("監控時間", datetime.now().strftime('%Y-%m-%d %H:%M'))

    
    # 系統資訊 (在頁面底部)
    with st.expander("ℹ️ 系統資訊", expanded=False):
        st.info(f"""
        EcoPort 智慧永續港平台
        - 版本: 2.0.0 
        - 建置日期: 2025-05-22
        - 功能模組: 動態碳排放監控、智慧能源管理、ESG評分、即時智慧警示、預測性維護
        - 技術架構: Python + Streamlit + Plotly + NumPy + Pandas
        - 智慧警示引擎: 動態閾值監控、趨勢分析、預測性警示
        - 資料更新頻率: 即時
        - 警示類別: 碳排放、能源效率、設備異常、環境監控、營運管理、ESG評分、預測性分析
        """)

if __name__ == "__main__":
    main()