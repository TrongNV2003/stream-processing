import pandas as pd

class DataLoader:
    def __init__(self):
        self.selected_columns = [
            'Protocol', 'Flow Duration', 'Tot Fwd Pkts', 'Tot Bwd Pkts', 
            'TotLen Fwd Pkts', 'TotLen Bwd Pkts', 'Fwd Pkt Len Max', 
            'Fwd Pkt Len Mean', 'Bwd Pkt Len Max', 'Flow Byts/s', 
            'Flow Pkts/s', 'Flow IAT Mean', 'Flow IAT Max', 'SYN Flag Cnt', 
            'RST Flag Cnt', 'PSH Flag Cnt', 'ACK Flag Cnt', 'Down/Up Ratio', 
            'Pkt Size Avg', 'Active Mean'
        ]
    
    def build_context(self, data: dict, sep_token: str) -> str:
        context_parts = []
        for col in self.selected_columns:
            value = data.get(col, 0)
            if isinstance(value, float) and (pd.isna(value) or value in [float('inf'), float('-inf')]):
                value = 0
            context_parts.append(f"{col.replace(' ', '_')}_is_{value}")
        return sep_token.join(context_parts)