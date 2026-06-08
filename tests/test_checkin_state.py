import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from checkin import (
	format_check_in_notification,
	format_failure_notification,
	format_notification_header,
	format_overall_summary,
	generate_balance_hash,
	get_github_run_url,
)


def test_balance_hash_changes_when_quota_changes():
	before = {'account_1': {'quota': 100.0, 'used': 20.0}}
	after = {'account_1': {'quota': 125.0, 'used': 20.0}}

	assert generate_balance_hash(before) != generate_balance_hash(after)


def test_balance_hash_changes_when_used_quota_changes():
	before = {'account_1': {'quota': 100.0, 'used': 20.0}}
	after = {'account_1': {'quota': 100.0, 'used': 21.0}}

	assert generate_balance_hash(before) != generate_balance_hash(after)


def test_balance_hash_is_stable_for_equivalent_balances():
	left = {
		'account_2': {'quota': 50.0, 'used': 1.0},
		'account_1': {'quota': 100.0, 'used': 20.0},
	}
	right = {
		'account_1': {'used': 20.0, 'quota': 100.0},
		'account_2': {'used': 1.0, 'quota': 50.0},
	}

	assert generate_balance_hash(left) == generate_balance_hash(right)


def test_github_run_url(monkeypatch):
	monkeypatch.setenv('GITHUB_REPOSITORY', 'GuDong2003/anyrouter-check-in')
	monkeypatch.setenv('GITHUB_RUN_ID', '123456')

	assert get_github_run_url() == 'https://github.com/GuDong2003/anyrouter-check-in/actions/runs/123456'


def test_notification_header_only_includes_execution_time(monkeypatch):
	monkeypatch.setenv('GITHUB_EVENT_NAME', 'workflow_dispatch')
	monkeypatch.setenv('GITHUB_REPOSITORY', 'GuDong2003/anyrouter-check-in')
	monkeypatch.setenv('GITHUB_RUN_ID', '123456')

	header = format_notification_header()

	assert header.startswith('⏰ 执行时间：')
	assert '🚀 触发方式' not in header
	assert '📣 推送原因' not in header
	assert '🔗 运行记录' not in header


def test_overall_summary_calculates_totals():
	details = {
		'account_1': {
			'success': True,
			'before_quota': 10,
			'before_used': 2,
			'after_quota': 11,
			'after_used': 2,
			'check_in_reward': 1,
			'usage_increase': 0,
			'balance_change': 1,
		},
		'account_2': {
			'success': True,
			'before_quota': 5,
			'before_used': 1,
			'after_quota': 5.5,
			'after_used': 1.2,
			'check_in_reward': 0.7,
			'usage_increase': 0.2,
			'balance_change': 0.5,
		},
	}

	summary = format_overall_summary(success_count=2, total_count=2, account_details=details)

	assert '✅ 成功：2/2  |  ❌ 失败：0/2' in summary
	assert '💰 总余额：$15.00 → $16.50' in summary
	assert '🎁 总奖励：+$1.70' in summary
	assert '📉 总消耗：$0.20' in summary
	assert '📈 净变化：+$1.50' in summary
	assert '🎉 全部账号签到成功！' in summary


def test_failure_notification_contains_reason_and_hint():
	message = format_failure_notification('账号 A', '登录失败')

	assert '❌ 账号 A' in message
	assert '原因：登录失败' in message
	assert '建议：检查 COOKIE / 邮箱密码 / 代理订阅' in message


def test_check_in_notification_compacts_no_change():
	message = format_check_in_notification({
		'name': 'Any Router - GuDong',
		'before_quota': 2760.45,
		'before_used': 914.55,
		'after_quota': 2760.45,
		'after_used': 914.55,
		'check_in_reward': 0,
		'usage_increase': 0,
		'balance_change': 0,
	})

	assert message == '\n'.join([
		'【签到】Any Router - GuDong',
		'  ━━━━━━━━━━━━━━━━━━━━',
		'     💵 余额: $2760.45  ｜  📊 累计消耗: $914.55',
		'  ━━━━━━━━━━━━━━━━━━━━',
		'  ℹ️  今日已签到，暂无变化',
	])


def test_check_in_notification_shows_balance_reward_change():
	message = format_check_in_notification({
		'name': 'Any Router - GuDong',
		'before_quota': 2760.45,
		'before_used': 914.55,
		'after_quota': 2761.45,
		'after_used': 914.55,
		'check_in_reward': 1,
		'usage_increase': 0,
		'balance_change': 1,
	})

	assert '     💵 余额: $2760.45 → $2761.45（+$1.00）' in message
	assert '     📊 累计消耗: $914.55' in message
	assert '  🎁 签到奖励: +$1.00' in message


def test_check_in_notification_shows_reward_and_usage_change():
	message = format_check_in_notification({
		'name': 'Any Router - GuDong',
		'before_quota': 2760.45,
		'before_used': 914.55,
		'after_quota': 2761.45,
		'after_used': 915.05,
		'check_in_reward': 1.5,
		'usage_increase': 0.5,
		'balance_change': 1,
	})

	assert '     💵 余额: $2760.45 → $2761.45（+$1.00）' in message
	assert '     📊 累计消耗: $914.55 → $915.05（+$0.50）' in message
	assert '  🎁 签到奖励: +$1.50  ｜  📉 期间消耗: $0.50' in message
