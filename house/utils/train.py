import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sqlalchemy import create_engine
from sklearn import preprocessing, model_selection
import warnings

warnings.filterwarnings('ignore')


def preprocess_house_data():
    engine = create_engine("mysql+pymysql://root:123456@localhost:3306/house?charset=utf8mb4")
    data = pd.read_sql_table(
        'houseinfo',
        con=engine,
        columns=['city', 'area', 'building_type', 'decoration', 'house_type', 'year', 'single_price', 'total_price']
    )
    engine.dispose()
    data.dropna(subset=data.columns, inplace=True)
    for column in data.select_dtypes(include=['object']):
        encoder = preprocessing.LabelEncoder()
        data[column] = encoder.fit_transform(data[column])
    x = data.iloc[:, :-2].values
    y = data.iloc[:, -2:].values
    scaler = preprocessing.StandardScaler()
    x = scaler.fit_transform(x)
    y_scaler = preprocessing.StandardScaler()
    y = y_scaler.fit_transform(y)
    train_x, test_x, train_y, test_y = model_selection.train_test_split(
        x, y, shuffle=True, random_state=7, test_size=0.2
    )
    return train_x, test_x, train_y, test_y


class HouseDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.tensor(x, dtype=torch.float32).unsqueeze(1)
        self.y = torch.tensor(y, dtype=torch.float32)

    def __len__(self):
        return len(self.x)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


class HouseLSTM(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=2, output_size=2):
        super(HouseLSTM, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, output_size)
        )

    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        out = out[:, -1, :]
        out = self.fc(out)
        return out


def train_model():
    train_x, test_x, train_y, test_y = preprocess_house_data()
    input_size = train_x.shape[1]
    train_dataset = HouseDataset(train_x, train_y)
    test_dataset = HouseDataset(test_x, test_y)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = HouseLSTM(input_size=input_size).to(device)

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    epochs = 10
    best_test_loss = float('inf')
    best_model_state = None  # 保存最优模型权重

    for epoch in range(epochs):
        total_loss = 0.0
        model.train()
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        print(f"Epoch [{epoch + 1}/{epochs}], Train Loss: {avg_loss:.4f}")

        # 验证阶段
        model.eval()
        test_loss = 0.0
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                test_loss += loss.item()

        avg_test_loss = test_loss / len(test_loader)
        print(f"Test Loss: {avg_test_loss:.4f}")

        if avg_test_loss < best_test_loss:
            best_test_loss = avg_test_loss
            best_model_state = model.state_dict().copy()  # 保存最优权重
            print(f"发现最优模型，测试损失：{best_test_loss:.4f}")

    model.load_state_dict(best_model_state)
    dummy_input = torch.randn(1, 1, input_size, dtype=torch.float32).to(device)
    torch.onnx.export(
        model, dummy_input, "../models/best_house_model.onnx",
        opset_version=12, input_names=['input'], output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"\n训练完成！最优测试损失：{best_test_loss:.4f}，ONNX模型已保存")


if __name__ == '__main__':
    train_model()