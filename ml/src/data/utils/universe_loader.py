"""
Universe YAML ローダーの統一モジュール
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


# デフォルトのセクターYAMLパス（config/sectors.yaml）
DEFAULT_SECTORS_YAML = Path(__file__).parent.parent.parent.parent / "config" / "sectors.yaml"


def load_sector_mapping(sectors_yaml_path: Optional[Path] = None) -> Dict[str, int]:
    """
    セクター定義YAMLを読み込み、セクター名からIDへのマッピングを返す

    Args:
        sectors_yaml_path: セクター定義YAMLのパス（Noneの場合はデフォルト）

    Returns:
        Dict[str, int]: セクター名 -> セクターID のマッピング

    Example:
        >>> mapping = load_sector_mapping()
        >>> print(mapping["Technology"])
        10
        >>> print(mapping["Unknown"])
        0
    """
    if sectors_yaml_path is None:
        sectors_yaml_path = DEFAULT_SECTORS_YAML

    sectors_yaml_path = Path(sectors_yaml_path)

    if not sectors_yaml_path.exists():
        raise FileNotFoundError(f"Sectors YAML not found: {sectors_yaml_path}")

    with open(sectors_yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    sectors = data.get("sectors", [])

    mapping = {}
    for sector in sectors:
        name = sector.get("name")
        sector_id = sector.get("id")
        if name is not None and sector_id is not None:
            mapping[name] = sector_id

    return mapping


def get_sector_id(sector_name: str, sector_mapping: Dict[str, int]) -> int:
    """
    セクター名からセクターIDを取得

    Args:
        sector_name: セクター名
        sector_mapping: セクター名 -> ID のマッピング

    Returns:
        int: セクターID（見つからない場合は0=Unknown）
    """
    return sector_mapping.get(sector_name, 0)


def load_universe_data(yaml_path: Path) -> Dict[str, Any]:
    """
    Universe YAMLをロードし、統一フォーマットで返す

    Args:
        yaml_path: Universe YAMLファイルのパス

    Returns:
        {
            "tickers": List[Dict[str, Any]],  # 各銘柄の詳細情報
            "ticker_list": List[str],          # ティッカー文字列リスト
        }

    Raises:
        ValueError: YAMLフォーマットが不正な場合
        FileNotFoundError: YAMLファイルが見つからない場合

    Example:
        >>> data = load_universe_data(Path("config/universes/my_universe.yaml"))
        >>> print(data["ticker_list"])
        ['2914.T', '4063.T', ...]
        >>> print(data["tickers"][0])
        {'ticker': '2914.T', 'sector': 'Consumer Defensive', ...}
    """
    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Universe YAML not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Handle both formats: 'tickers' or 'universe' key
    if "universe" in data:
        tickers = data["universe"]
    elif "tickers" in data:
        tickers = data["tickers"]
    else:
        raise ValueError(
            f"Invalid universe YAML format: expected 'tickers' or 'universe' key in {yaml_path}"
        )

    # Ensure all items are dictionaries with 'ticker' key
    ticker_list = []
    for item in tickers:
        if isinstance(item, dict):
            if "ticker" not in item:
                raise ValueError(f"Ticker entry missing 'ticker' key: {item}")
            ticker_list.append(item["ticker"])
        elif isinstance(item, str):
            # Simple string format - convert to dict
            ticker_list.append(item)
            # Convert to dict format for consistency
            tickers = [{"ticker": t} if isinstance(t, str) else t for t in tickers]
        else:
            raise ValueError(f"Invalid ticker format: {item}")

    return {
        "tickers": tickers,
        "ticker_list": ticker_list,
    }


def get_tickers_from_universe_yaml(yaml_path: Path) -> List[str]:
    """
    Universe YAMLからティッカーリストを取得（後方互換性のため）

    Args:
        yaml_path: Universe YAMLファイルのパス

    Returns:
        List[str]: ティッカーリスト

    Example:
        >>> tickers = get_tickers_from_universe_yaml(Path("config/universes/my_universe.yaml"))
        >>> print(tickers)
        ['2914.T', '4063.T', ...]
    """
    data = load_universe_data(yaml_path)
    return data["ticker_list"]
