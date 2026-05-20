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

            if data.empty or len(data) < 3:
                continue

            #Organizar os dados
            data = data.reset_index()
            first_price_col = data.columns[1]  # depois do Date
            data.loc[0, first_price_col] = data.loc[2, first_price_col]
            data = data.drop(index=1).reset_index(drop=True)
            filename = os.path.join(data_dir, f"{ticker.replace('-', '_')}.csv")
            data.to_csv(filename)

            print(f"🛠 {ticker}: {len(data)} registros salvos em {filename}")

        except Exception as e:
            print(f"❌ Erro ao baixar {ticker}: {str(e)}")

    # Mostrar resumo dos arquivos criados
    if os.path.exists(data_dir):
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        for file in sorted(csv_files):
            file_path = os.path.join(data_dir, file)

