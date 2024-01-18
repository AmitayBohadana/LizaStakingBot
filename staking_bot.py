import threading
from datetime import time
import logging
import asyncio
from web3 import Web3
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

# Your bot token from BotFather
TELEGRAM_BOT_TOKEN = '6625329190:AAHBTirm09PJ1gjf0KYfqHVbIsFgatatNc4'
CHANNEL_ID = '-1001904357027'
CHANNEL_ID_TEMP = '-4105097249'

# Ethereum node connection string (use Infura or similar)
WEB3_PROVIDER_URI = 'wss://mainnet.infura.io/ws/v3/73574fcd80f047ad8251715b662fca69'

# Staking contract ABI and addresses
STAKING_CONTRACT_ABI = [
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_token",
          "type": "address"
        },
        {
          "internalType": "uint256",
          "name": "_lockupPeriod",
          "type": "uint256"
        },
        {
          "internalType": "address",
          "name": "__router",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "_uniswapUsdEthPair",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "_teamWallet",
          "type": "address"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "previousOwner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "OwnershipTransferred",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amountTokens",
          "type": "uint256"
        }
      ],
      "name": "PoolHasBeenFunded",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "Staked",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "address",
          "name": "user",
          "type": "address"
        }
      ],
      "name": "StakingRewardClaimed",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        }
      ],
      "name": "Unstaked",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        },
        {
          "indexed": False,
          "internalType": "bool",
          "name": "_wasCompounded",
          "type": "bool"
        }
      ],
      "name": "rewardDistributed",
      "type": "event"
    },
    {
      "inputs": [
        {
          "internalType": "bool",
          "name": "_compound",
          "type": "bool"
        },
        {
          "internalType": "uint256",
          "name": "_compMinTokensToReceive",
          "type": "uint256"
        }
      ],
      "name": "claimReward",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_wallet",
          "type": "address"
        },
        {
          "internalType": "bool",
          "name": "_compound",
          "type": "bool"
        },
        {
          "internalType": "uint256",
          "name": "_compMinTokensToReceive",
          "type": "uint256"
        }
      ],
      "name": "claimRewardAdmin",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "fundPoolWithRewards",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getCurrentFeeInETH",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getETHPrice",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "wallet",
          "type": "address"
        }
      ],
      "name": "getUnpaid",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "lockupPeriod",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "renounceOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "rewardsRatePerShare",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "_uniswapUsdEthPair",
          "type": "address"
        },
        {
          "internalType": "address",
          "name": "_teamWallet",
          "type": "address"
        }
      ],
      "name": "setAddresses",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_seconds",
          "type": "uint256"
        }
      ],
      "name": "setLockupPeriod",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "contract ITokenStakingPoolExtension",
          "name": "_tokenStakingPool",
          "type": "address"
        }
      ],
      "name": "setPoolExtension",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_newFeeUSD",
          "type": "uint256"
        }
      ],
      "name": "setTargetFeeUSD",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        }
      ],
      "name": "stake",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address[]",
          "name": "_wallets",
          "type": "address[]"
        },
        {
          "internalType": "uint256[]",
          "name": "_amounts",
          "type": "uint256[]"
        }
      ],
      "name": "stakeForWallets",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "stakerRewards",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "excluded",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "realised",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "stakerShares",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "amount",
          "type": "uint256"
        },
        {
          "internalType": "uint256",
          "name": "lastStakeTime",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "targetFeeUSD",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "teamWallet",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "token",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "tokenStakingPool",
      "outputs": [
        {
          "internalType": "contract ITokenStakingPoolExtension",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalRewardDistributed",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalRewards",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalStakedShares",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "totalStakers",
      "outputs": [
        {
          "internalType": "uint256",
          "name": "",
          "type": "uint256"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "uniswapUsdEthPair",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        }
      ],
      "name": "unstake",
      "outputs": [],
      "stateMutability": "payable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "uint256",
          "name": "_amount",
          "type": "uint256"
        }
      ],
      "name": "withdrawTokens",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
  ]
STAKING_CONTRACT_ADDRESSES = ['0x27d72E38C23bdCacAb5b31F58627393097bd846a', '0xD8485d7F825a7cBABfAcF6AE0c21a6D4Feb0d98D','0x316aE40E5AB26D0Dd6DecD4E6AC3a6f26ECddaeE','0x7eB2A1697E5B5D36dcF4BB1861B639dC5505e1d6']  # Replace with your contract addresses

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
# Set up the Web3 connection
web3 = Web3(Web3.WebsocketProvider(WEB3_PROVIDER_URI))

# Set up the Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)

def fetch_usd_price(token_symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_symbol}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data.get(token_symbol, {}).get('usd', None)
    except Exception as e:
        logger.error(f"Error fetching USD price: {e}")
        return None

def escape_markdown(text):
    """Escape markdown characters."""
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)
# Function to handle new stake events

def get_total_staked_from_contract(contract_address, contract_abi):
  contract = web3.eth.contract(address=contract_address, abi=contract_abi)
  total_staked_raw = contract.functions.totalStakedShares().call()
  return total_staked_raw / (10 ** 18)  # Adjust for token decimals if necessary
def handle_event(event, contract):
    try:
        # Define your custom emojis
        amount_staked_emoji = '👍'  # Replace with your chosen emoji for amount staked
        duration_emoji = '⏰'  # Replace with your chosen emoji for duration
        total_staked_emoji = '🔒'  # Replace with your chosen emoji for total staked
        # Convert the amount staked to a proper decimal by dividing by 10**18 and format to 2 decimal places
        amount_staked = event['args']['amount'] / (10 ** 18)  # Adjust for token decimals
        # Fetch the USD price of $LIZA
        liza_usd_price = fetch_usd_price('liza-2')  # Replace 'liza' with the actual ID used by CoinGecko for Liza token



        print("liza_usd_price: ",liza_usd_price)

        # Format the staking information
        robot_emoji = '🤖'
        amount_staked_formatted = f"{amount_staked:,.2f}"  # Format with comma separators and 2 decimal places
        # Fetch lockupPeriod from the contract and convert it to days
        lockup_period_seconds = contract.functions.lockupPeriod().call()
        duration_days = lockup_period_seconds // (24 * 60 * 60)  # Convert seconds to days

        # Fetch totalStakedShares from the contract and adjust for decimals
        total_staked_shares_raw = contract.functions.totalStakedShares().call()
        # Assuming totalStakedShares also uses 18 decimals, format it similarly
        # Initialize total staked across all contracts
        total_staked_across_all_contracts = 0

        # Iterate over each contract address and sum the total staked
        for address in STAKING_CONTRACT_ADDRESSES:
          total_staked_across_all_contracts += get_total_staked_from_contract(address, STAKING_CONTRACT_ABI)

        total_staked_shares_formatted = f"{total_staked_across_all_contracts:,.2f}"  # Format with comma separators and 2 decimal places

        # Check if price data is available
        if liza_usd_price is not None:
            usd_value = amount_staked * liza_usd_price
            usd_value_formatted = f"${usd_value:,.2f}"
            total_staked_usd_value = total_staked_across_all_contracts * liza_usd_price
            total_staked_usd_value_formatted = f"${total_staked_usd_value:,.2f}"
        else:
            usd_value_formatted = ""
            total_staked_usd_value_formatted = ""

        # Relative path to your video
        video_path = 'liza_staking_video.mp4'  # Since the video is in the same directory as the script

        # Escape Markdown characters in the caption
        caption = (
            f"🎉 *NEW \\$LIZA STAKE\\!* 🎉\n\n"
            f"{robot_emoji} *Amount Staked:*\n"
            f"{escape_markdown(amount_staked_formatted)} \\$LIZA \\| {escape_markdown(usd_value_formatted)}\n\n"
            f"{duration_emoji} *Duration:*\n"
            f"{duration_days} days\n\n"
            f"{total_staked_emoji} *Total Staked:*\n"
            f"{escape_markdown(total_staked_shares_formatted)} \\$LIZA \\| {escape_markdown(total_staked_usd_value_formatted)}\n"
        )

        transaction_hash_bytes = event['transactionHash']
        transaction_hash_hex = transaction_hash_bytes.hex()  # Convert bytes to hex string

        print("transaction hash: _",transaction_hash_hex)
        # Ensure that the URL starts with https://
        etherscan_url = f"https://etherscan.io/tx/{transaction_hash_hex}"

        # Ensure that the staking URL is correct and starts with https://
        staking_url = "https://lizatoken.com/staking/"
        # Define emojis for buttons
        chain_emoji = '🌐'  # Chain emoji for the transaction button
        lock_emoji = '🔒'  # Lock emoji for the staking button
        # Create inline keyboard with buttons
        keyboard = [
            [InlineKeyboardButton(f"{chain_emoji} View On Etherscan", url=etherscan_url)],
            [InlineKeyboardButton(f"{lock_emoji} Stake Here!", url=staking_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Escape Markdown characters in the caption
        # ... (the previous code for caption formatting stays the same)

        # Send the video with the caption and buttons
        bot.send_video(chat_id=CHANNEL_ID, video=open(video_path, 'rb'), caption=caption,
                       parse_mode='MarkdownV2', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in handle_event: {e}")


# Async function to poll for new events
async def log_loop(event_filter, poll_interval, contract):
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event, contract)
        await asyncio.sleep(poll_interval)


# Create and run tasks for each contract
async def main():
    tasks = []
    for address in STAKING_CONTRACT_ADDRESSES:
        contract = web3.eth.contract(address=address, abi=STAKING_CONTRACT_ABI)
        event_filter = contract.events.Staked.create_filter(fromBlock='latest')
        tasks.append(asyncio.create_task(log_loop(event_filter, 2, contract)))

    await asyncio.gather(*tasks)


# Start the bot and send a hello message
updater.start_polling()

# Start the bot
updater.start_polling()

# Run the main function using asyncio
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error in main function: {e}")
