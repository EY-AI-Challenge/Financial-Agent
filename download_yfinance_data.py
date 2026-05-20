import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta


def download_financial_data(
    stocks: list[str] | None = None,
    crypto: list[str] | None = None
):
    if stocks is None:
        stocks = ['AMZN', 'AAPL', 'GOOGL', 'MSFT', 'UDMY', 'NXE', 'SPY', 'CDR.WA', 'EH']

    if crypto is None:
        crypto = ['BTC-USD', 'ETH-USD']
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Diretório '{data_dir}' criado.")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=5 * 365)

    # Download dos dados
    all_tickers = stocks + crypto

    for ticker in all_tickers:
        try:

            # Download dos dados
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)

            if data.empty:
                continue

            # Salvar em CSV
            filename = os.path.join(data_dir, f"{ticker.replace('-', '_')}.csv")
            data.to_csv(filename)

            print(f"✅ {ticker}: {len(data)} registros salvos em {filename}")

        except Exception as e:
            print(f" Erro ao baixar {ticker}: {str(e)}")

    # Mostrar resumo dos arquivos criados
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        for file in sorted(csv_files):
            file_path = os.path.join(data_dir, file)


def create_combined_dataset():
    data_dir = 'data'
    combined_file = os.path.join(data_dir, 'combined_financial_data.csv')

    if not os.path.exists(data_dir):
        return

    all_data = {}

    # Ler todos os arquivos CSV
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and f != 'combined_financial_data.csv']

    for file in csv_files:
        ticker = file.replace('.csv', '').replace('_', '-')
        file_path = os.path.join(data_dir, file)
        # trocar primeira entrada pela terceira
        df.iloc[0, 0] = df.iloc[2, 0]

        # apagar terceira linha
        df = df.drop(index=df.index[2]).reset_index(drop=True)
        try:
            df = pd.read_csv(file_path, index_col='Date', parse_dates=True)


            all_data[ticker] = df['Close']
        except Exception as e:
            print(f"Erro ao ler {file}: {str(e)}")

    if all_data:
        # Criar DataFrame combinado
        combined_df = pd.DataFrame(all_data)

        # Salvar dataset combinado
        combined_df.to_csv(combined_file)


if __name__ == "__main__":
    # Download dos dados individuais
    download_financial_data()

    # Criar dataset combinado
    create_combined_dataset()
    
