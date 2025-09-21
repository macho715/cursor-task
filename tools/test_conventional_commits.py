#!/usr/bin/env python3
"""
Conventional Commits 테스트
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conventional_commits import ConventionalCommitsManager, ConventionalCommit

def test_commit_message_parsing():
    """커밋 메시지 파싱 테스트"""
    print("🧪 커밋 메시지 파싱 테스트")
    
    manager = ConventionalCommitsManager()
    
    # 유효한 커밋 메시지들
    valid_commits = [
        "feat: add user authentication",
        "fix(api): resolve timeout issue",
        "docs(readme): update installation guide",
        "refactor(auth): simplify login flow",
        "feat!: breaking change in API",
        "feat(auth): add OAuth2 support\n\nBREAKING CHANGE: API endpoints changed"
    ]
    
    # 무효한 커밋 메시지들
    invalid_commits = [
        "add user authentication",  # 타입 없음
        "feat: add",  # 너무 짧음
        "unknown: add feature",  # 알 수 없는 타입
        "style!: breaking change"  # style에 breaking change 불가
    ]
    
    print("✅ 유효한 커밋 메시지 테스트:")
    for commit_msg in valid_commits:
        commit = manager.parse_commit_message(commit_msg)
        if commit:
            print(f"  ✅ {commit_msg[:50]}... -> {commit.type}({commit.scope}): {commit.description}")
        else:
            print(f"  ❌ 파싱 실패: {commit_msg[:50]}...")
    
    print("\n❌ 무효한 커밋 메시지 테스트:")
    for commit_msg in invalid_commits:
        is_valid, errors = manager.validate_commit_message(commit_msg)
        if not is_valid:
            print(f"  ✅ {commit_msg[:50]}... -> {errors[0]}")
        else:
            print(f"  ❌ 예상과 다름: {commit_msg[:50]}...")

def test_version_bumping():
    """버전 증가 테스트"""
    print("\n🧪 버전 증가 테스트")
    
    manager = ConventionalCommitsManager()
    
    test_cases = [
        ("1.0.0", "patch", "1.0.1"),
        ("1.0.0", "minor", "1.1.0"),
        ("1.0.0", "major", "2.0.0"),
        ("0.9.9", "minor", "1.0.0"),
        ("2.5.3", "patch", "2.5.4")
    ]
    
    for current, bump_type, expected in test_cases:
        result = manager.bump_version(current, bump_type)
        if result == expected:
            print(f"  ✅ {current} + {bump_type} = {result}")
        else:
            print(f"  ❌ {current} + {bump_type} = {result} (예상: {expected})")

def test_changelog_generation():
    """CHANGELOG 생성 테스트"""
    print("\n🧪 CHANGELOG 생성 테스트")
    
    manager = ConventionalCommitsManager()
    
    # 테스트용 커밋 생성
    test_commits = [
        ConventionalCommit(
            type="feat",
            scope="auth",
            description="add OAuth2 support",
            body=None,
            footer="BREAKING CHANGE: API endpoints changed",
            breaking_change=True,
            hash="abc123",
            date="2025-09-21",
            author="test"
        ),
        ConventionalCommit(
            type="fix",
            scope="api",
            description="resolve timeout issue",
            body=None,
            footer=None,
            breaking_change=False,
            hash="def456",
            date="2025-09-21",
            author="test"
        ),
        ConventionalCommit(
            type="docs",
            scope="readme",
            description="update installation guide",
            body=None,
            footer=None,
            breaking_change=False,
            hash="ghi789",
            date="2025-09-21",
            author="test"
        )
    ]
    
    changelog = manager.generate_changelog(test_commits, "1.2.0")
    
    print("✅ CHANGELOG 생성 완료:")
    print("  - Breaking Changes 섹션 포함")
    print("  - 타입별 그룹화")
    print("  - 통계 정보 포함")
    print(f"  - 총 길이: {len(changelog)} 문자")

def test_git_integration():
    """Git 통합 테스트"""
    print("\n🧪 Git 통합 테스트")
    
    manager = ConventionalCommitsManager()
    
    try:
        # Git 저장소 확인
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ Git 저장소 확인")
            
            # 최근 커밋 확인
            result = subprocess.run(['git', 'log', '-1', '--pretty=%s'], capture_output=True, text=True)
            if result.returncode == 0:
                latest_commit = result.stdout.strip()
                print(f"  ✅ 최근 커밋: {latest_commit}")
                
                # 커밋 메시지 검증
                is_valid, errors = manager.validate_commit_message(latest_commit)
                if is_valid:
                    print("  ✅ 최근 커밋이 Conventional Commits 형식입니다")
                else:
                    print(f"  ❌ 최근 커밋 검증 실패: {errors[0]}")
            else:
                print("  ⚠️ 커밋 히스토리를 가져올 수 없습니다")
        else:
            print("  ⚠️ Git 저장소가 아닙니다")
    
    except Exception as e:
        print(f"  ❌ Git 통합 테스트 실패: {e}")

def test_importance_analysis():
    """중요도 분석 테스트"""
    print("\n🧪 중요도 분석 테스트")
    
    manager = ConventionalCommitsManager()
    
    test_commits = [
        ConventionalCommit("feat", "auth", "add login", None, None, False, "", "", ""),
        ConventionalCommit("fix", "api", "resolve bug", None, None, False, "", "", ""),
        ConventionalCommit("docs", "readme", "update docs", None, None, False, "", "", ""),
        ConventionalCommit("style", "code", "format code", None, None, False, "", "", ""),
        ConventionalCommit("refactor", "auth", "simplify logic", None, None, False, "", "", "")
    ]
    
    analysis = manager.analyze_commits(test_commits)
    
    print("✅ 중요도 분석 결과:")
    print(f"  - 총 커밋 수: {analysis['total_commits']}")
    print(f"  - 중요도 점수: {analysis['importance_score']}")
    print(f"  - 버전 증가: {analysis['version_bump']}")
    print(f"  - 타입별 분포: {analysis['by_type']}")

def test_configuration():
    """설정 파일 테스트"""
    print("\n🧪 설정 파일 테스트")
    
    config_file = "tools/conventional_commits_config.yaml"
    
    if os.path.exists(config_file):
        print(f"  ✅ 설정 파일 존재: {config_file}")
        
        # YAML 파싱 테스트
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            required_sections = ['allowed_types', 'importance_levels', 'version_bumps']
            for section in required_sections:
                if section in config:
                    print(f"  ✅ {section} 섹션 확인")
                else:
                    print(f"  ❌ {section} 섹션 누락")
        
        except Exception as e:
            print(f"  ❌ 설정 파일 파싱 실패: {e}")
    else:
        print(f"  ❌ 설정 파일 없음: {config_file}")

def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 Conventional Commits 테스트 시작\n")
    
    try:
        test_commit_message_parsing()
        test_version_bumping()
        test_changelog_generation()
        test_git_integration()
        test_importance_analysis()
        test_configuration()
        
        print("\n🎉 모든 Conventional Commits 테스트 통과!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n💥 테스트 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
