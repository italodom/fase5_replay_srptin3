"""
Componente de Card para exibir informações de uma estufa
"""
import streamlit as st
from typing import Dict, Optional


class EstufaCard:
    """Componente visual para exibir dados de uma estufa"""

    # Cores por status
    COLORS = {
        'Normal': '#28a745',    # Verde
        'Alerta': '#ffc107',    # Amarelo
        'Critico': '#dc3545'    # Vermelho
    }

    # Emojis por status
    EMOJIS = {
        'Normal': '✅',
        'Alerta': '⚠️',
        'Critico': '🚨'
    }

    @classmethod
    def render(cls, estufa_data: Dict):
        """
        Renderiza um card de estufa

        Args:
            estufa_data: Dicionário com dados da estufa
        """
        nome = estufa_data.get('nome', 'Estufa')
        cultura = estufa_data.get('cultura', 'N/A')
        temperatura = estufa_data.get('temperatura')
        umidade = estufa_data.get('umidade')
        status = estufa_data.get('status', 'Normal')

        # Cor baseada no status
        color = cls.COLORS.get(status, '#6c757d')
        emoji = cls.EMOJIS.get(status, '❓')

        # Card com borda colorida (sem fundo)
        st.markdown(f"""
            <div style="
                border-left: 5px solid {color};
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
            ">
                <h3 style="margin: 0; color: #333;">{emoji} {nome}</h3>
                <p style="margin: 5px 0; color: #666;">📍 Cultura: <strong>{cultura}</strong></p>
                <hr style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-around;">
                    <div style="text-align: center;">
                        <p style="margin: 0; font-size: 0.9em; color: #666;">🌡️ Temperatura</p>
                        <p style="margin: 5px 0; font-size: 1.5em; font-weight: bold; color: #333;">
                            {temperatura:.1f}°C
                        </p>
                    </div>
                    <div style="text-align: center;">
                        <p style="margin: 0; font-size: 0.9em; color: #666;">💧 Umidade</p>
                        <p style="margin: 5px 0; font-size: 1.5em; font-weight: bold; color: #333;">
                            {umidade:.1f}%
                        </p>
                    </div>
                </div>
                <hr style="margin: 10px 0;">
                <p style="margin: 0; text-align: center; font-weight: bold; color: {color};">
                    Status: {status.upper()}
                </p>
            </div>
        """, unsafe_allow_html=True)

    @classmethod
    def render_simple_metric(cls, label: str, value: str, status: str = 'Normal'):
        """
        Renderiza uma métrica simples

        Args:
            label: Rótulo da métrica
            value: Valor a exibir
            status: Status (Normal, Alerta, Critico)
        """
        color = cls.COLORS.get(status, '#6c757d')
        st.markdown(f"""
            <div style="
                padding: 10px;
                background-color: {color};
                color: white;
                border-radius: 5px;
                text-align: center;
            ">
                <p style="margin: 0; font-size: 0.9em;">{label}</p>
                <p style="margin: 5px 0; font-size: 1.3em; font-weight: bold;">{value}</p>
            </div>
        """, unsafe_allow_html=True)
