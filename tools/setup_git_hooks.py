#!/usr/bin/env python3
"""
Git 훅 설정 스크립트
Conventional Commits 자동 검증을 위한 Git 훅 설치

사용법:
    python tools/setup_git_hooks.py --install
    python tools/setup_git_hooks.py --uninstall
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def get_git_hooks_dir():
    """Git 훅 디렉토리 경로 반환"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, check=True)
        git_dir = result.stdout.strip()
        return os.path.join(git_dir, 'hooks')
    except subprocess.CalledProcessError:
        print("❌ Git 저장소가 아닙니다.")
        sys.exit(1)

def create_commit_msg_hook():
    """commit-msg 훅 생성"""
    hook_content = '''#!/bin/bash
# Conventional Commits 검증 훅

# 커밋 메시지 파일 경로
COMMIT_MSG_FILE=$1

# Python 스크립트로 검증
python tools/conventional_commits.py --validate < "$COMMIT_MSG_FILE"

# 검증 결과 확인
if [ $? -ne 0 ]; then
    echo "❌ 커밋 메시지가 Conventional Commits 형식을 따르지 않습니다."
    echo "📖 형식: type(scope): description"
    echo "   예시: feat(auth): add user authentication"
    echo "   예시: fix(api): resolve timeout issue"
    echo "   예시: docs(readme): update installation guide"
    exit 1
fi

echo "✅ 커밋 메시지 검증 통과"
exit 0
'''
    return hook_content

def create_pre_commit_hook():
    """pre-commit 훅 생성"""
    hook_content = '''#!/bin/bash
# Pre-commit 검증 훅

echo "🔍 Pre-commit 검사 시작..."

# Python 파일 문법 검사
echo "📝 Python 파일 문법 검사..."
python_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.py$')
if [ -n "$python_files" ]; then
    for file in $python_files; do
        python -m py_compile "$file"
        if [ $? -ne 0 ]; then
            echo "❌ $file 문법 오류 발견"
            exit 1
        fi
    done
fi

# JSON 파일 검증
echo "📄 JSON 파일 검증..."
json_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.json$')
if [ -n "$json_files" ]; then
    for file in $json_files; do
        python -m json.tool "$file" > /dev/null
        if [ $? -ne 0 ]; then
            echo "❌ $file JSON 형식 오류 발견"
            exit 1
        fi
    done
fi

# YAML 파일 검증
echo "📋 YAML 파일 검증..."
yaml_files=$(git diff --cached --name-only --diff-filter=ACM | grep '\\.ya?ml$')
if [ -n "$yaml_files" ]; then
    for file in $yaml_files; do
        python -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "❌ $file YAML 형식 오류 발견"
            exit 1
        fi
    done
fi

echo "✅ Pre-commit 검사 완료"
exit 0
'''
    return hook_content

def create_post_commit_hook():
    """post-commit 훅 생성"""
    hook_content = '''#!/bin/bash
# Post-commit 훅

echo "📊 커밋 후 작업 수행..."

# 최근 커밋 정보 출력
echo "📝 최근 커밋:"
git log -1 --pretty=format:"  %s"

# CHANGELOG 업데이트 제안
echo "💡 CHANGELOG 업데이트를 원하시면 다음 명령어를 실행하세요:"
echo "   python tools/conventional_commits.py --generate-changelog"

# 릴리즈 생성 제안
echo "🚀 릴리즈 생성을 원하시면 다음 명령어를 실행하세요:"
echo "   python tools/conventional_commits.py --create-release"
'''
    return hook_content

def install_hooks():
    """Git 훅 설치"""
    hooks_dir = get_git_hooks_dir()
    
    print(f"🔧 Git 훅 설치 중: {hooks_dir}")
    
    # 훅 디렉토리 생성
    os.makedirs(hooks_dir, exist_ok=True)
    
    # commit-msg 훅
    commit_msg_hook = os.path.join(hooks_dir, 'commit-msg')
    with open(commit_msg_hook, 'w', encoding='utf-8') as f:
        f.write(create_commit_msg_hook())
    os.chmod(commit_msg_hook, 0o755)
    
    # pre-commit 훅
    pre_commit_hook = os.path.join(hooks_dir, 'pre-commit')
    with open(pre_commit_hook, 'w', encoding='utf-8') as f:
        f.write(create_pre_commit_hook())
    os.chmod(pre_commit_hook, 0o755)
    
    # post-commit 훅
    post_commit_hook = os.path.join(hooks_dir, 'post-commit')
    with open(post_commit_hook, 'w', encoding='utf-8') as f:
        f.write(create_post_commit_hook())
    os.chmod(post_commit_hook, 0o755)
    
    print("✅ Git 훅 설치 완료:")
    print("  - commit-msg: Conventional Commits 검증")
    print("  - pre-commit: 파일 형식 검증")
    print("  - post-commit: 커밋 후 안내")

def uninstall_hooks():
    """Git 훅 제거"""
    hooks_dir = get_git_hooks_dir()
    
    print(f"🗑️ Git 훅 제거 중: {hooks_dir}")
    
    hooks_to_remove = ['commit-msg', 'pre-commit', 'post-commit']
    
    for hook_name in hooks_to_remove:
        hook_path = os.path.join(hooks_dir, hook_name)
        if os.path.exists(hook_path):
            os.remove(hook_path)
            print(f"  ✅ {hook_name} 제거 완료")
        else:
            print(f"  ⚠️ {hook_name} 파일이 존재하지 않음")
    
    print("✅ Git 훅 제거 완료")

def list_hooks():
    """설치된 훅 목록 출력"""
    hooks_dir = get_git_hooks_dir()
    
    print(f"📋 설치된 Git 훅 목록: {hooks_dir}")
    
    if not os.path.exists(hooks_dir):
        print("❌ 훅 디렉토리가 존재하지 않습니다.")
        return
    
    hooks = ['commit-msg', 'pre-commit', 'post-commit']
    
    for hook_name in hooks:
        hook_path = os.path.join(hooks_dir, hook_name)
        if os.path.exists(hook_path):
            stat = os.stat(hook_path)
            executable = "✅" if stat.st_mode & 0o111 else "❌"
            print(f"  {executable} {hook_name}")
        else:
            print(f"  ❌ {hook_name} (설치되지 않음)")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Git 훅 설정 도구')
    parser.add_argument('--install', action='store_true', help='Git 훅 설치')
    parser.add_argument('--uninstall', action='store_true', help='Git 훅 제거')
    parser.add_argument('--list', action='store_true', help='설치된 훅 목록 출력')
    
    args = parser.parse_args()
    
    if args.install:
        install_hooks()
    elif args.uninstall:
        uninstall_hooks()
    elif args.list:
        list_hooks()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
