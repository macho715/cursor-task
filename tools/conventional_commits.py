#!/usr/bin/env python3
"""
Conventional Commits 자동화 및 릴리즈 태그 연동
외부 레퍼런스: https://www.conventionalcommits.org/en/v1.0.0/

사용법:
    python tools/conventional_commits.py --validate
    python tools/conventional_commits.py --generate-changelog
    python tools/conventional_commits.py --create-release
"""

import json
import argparse
import sys
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConventionalCommit:
    """Conventional Commit 구조"""
    type: str
    scope: Optional[str]
    description: str
    body: Optional[str]
    footer: Optional[str]
    breaking_change: bool
    hash: str
    date: str
    author: str

class ConventionalCommitsManager:
    """Conventional Commits 관리자"""
    
    def __init__(self):
        # 허용된 타입들 (Conventional Commits 스펙)
        self.allowed_types = {
            'feat': '새로운 기능',
            'fix': '버그 수정',
            'docs': '문서 변경',
            'style': '코드 스타일 변경 (포맷팅, 세미콜론 등)',
            'refactor': '리팩토링 (기능 변경 없음)',
            'perf': '성능 개선',
            'test': '테스트 추가/수정',
            'build': '빌드 시스템 변경',
            'ci': 'CI/CD 설정 변경',
            'chore': '기타 작업 (빌드, 설정 등)',
            'revert': '이전 커밋 되돌리기'
        }
        
        # 중요도별 분류
        self.importance_levels = {
            'feat': 3,      # 높음 - 새 기능
            'fix': 3,       # 높음 - 버그 수정
            'perf': 2,      # 중간 - 성능 개선
            'refactor': 2,  # 중간 - 리팩토링
            'docs': 1,      # 낮음 - 문서
            'style': 1,     # 낮음 - 스타일
            'test': 1,      # 낮음 - 테스트
            'build': 1,     # 낮음 - 빌드
            'ci': 1,        # 낮음 - CI
            'chore': 1,     # 낮음 - 기타
            'revert': 2     # 중간 - 되돌리기
        }
        
        # Breaking Change 키워드
        self.breaking_keywords = ['BREAKING CHANGE', 'BREAKING:', '!']
        
        # 릴리즈 타입별 버전 증가
        self.version_bumps = {
            'major': ['feat', 'fix'],  # BREAKING CHANGE 포함 시
            'minor': ['feat'],         # 새로운 기능
            'patch': ['fix', 'perf', 'refactor', 'docs', 'style', 'test', 'build', 'ci', 'chore']  # 기타
        }
    
    def parse_commit_message(self, commit_msg: str) -> Optional[ConventionalCommit]:
        """커밋 메시지를 Conventional Commit 형식으로 파싱"""
        lines = commit_msg.strip().split('\n')
        if not lines:
            return None
        
        # 첫 번째 라인 파싱 (헤더)
        header = lines[0]
        header_match = re.match(r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$', header)
        
        if not header_match:
            return None
        
        commit_type, scope, breaking_marker, description = header_match.groups()
        
        # Breaking Change 확인
        breaking_change = breaking_marker == '!' or any(
            keyword in commit_msg for keyword in self.breaking_keywords
        )
        
        # 본문과 푸터 분리
        body_lines = []
        footer_lines = []
        
        if len(lines) > 1:
            in_footer = False
            for line in lines[1:]:
                if line.startswith('BREAKING CHANGE') or line.startswith('BREAKING:'):
                    in_footer = True
                    footer_lines.append(line)
                elif in_footer:
                    footer_lines.append(line)
                elif line.strip():
                    body_lines.append(line)
                else:
                    in_footer = True
        
        return ConventionalCommit(
            type=commit_type,
            scope=scope,
            description=description,
            body='\n'.join(body_lines) if body_lines else None,
            footer='\n'.join(footer_lines) if footer_lines else None,
            breaking_change=breaking_change,
            hash='',  # Git에서 가져올 예정
            date='',  # Git에서 가져올 예정
            author=''  # Git에서 가져올 예정
        )
    
    def validate_commit_message(self, commit_msg: str) -> Tuple[bool, List[str]]:
        """커밋 메시지 유효성 검사"""
        errors = []
        
        if not commit_msg.strip():
            errors.append("커밋 메시지가 비어있습니다")
            return False, errors
        
        commit = self.parse_commit_message(commit_msg)
        if not commit:
            errors.append("Conventional Commits 형식이 아닙니다. 형식: type(scope): description")
            return False, errors
        
        # 타입 검증
        if commit.type not in self.allowed_types:
            errors.append(f"알 수 없는 타입: {commit.type}. 허용된 타입: {', '.join(self.allowed_types.keys())}")
        
        # 설명 길이 검증
        if len(commit.description) < 10:
            errors.append("설명이 너무 짧습니다 (최소 10자)")
        
        if len(commit.description) > 100:
            errors.append("설명이 너무 깁니다 (최대 100자)")
        
        # Breaking Change 검증
        if commit.breaking_change and commit.type not in ['feat', 'fix']:
            errors.append("Breaking Change는 feat 또는 fix 타입에서만 허용됩니다")
        
        return len(errors) == 0, errors
    
    def get_git_commits(self, since: Optional[str] = None, until: Optional[str] = None) -> List[ConventionalCommit]:
        """Git 커밋 히스토리 가져오기"""
        try:
            # Git 커밋 목록 가져오기
            cmd = ['git', 'log', '--pretty=format:%H|%ad|%an|%s|%b', '--date=iso']
            
            if since:
                cmd.extend(['--since', since])
            if until:
                cmd.extend(['--until', until])
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) >= 4:
                    hash_val, date, author, subject, body = parts[0], parts[1], parts[2], parts[3], parts[4] if len(parts) > 4 else ''
                    
                    # 커밋 메시지 재구성
                    commit_msg = subject
                    if body:
                        commit_msg += '\n\n' + body
                    
                    commit = self.parse_commit_message(commit_msg)
                    if commit:
                        commit.hash = hash_val
                        commit.date = date
                        commit.author = author
                        commits.append(commit)
            
            return commits
            
        except subprocess.CalledProcessError as e:
            print(f"Git 명령어 실행 실패: {e}")
            return []
    
    def analyze_commits(self, commits: List[ConventionalCommit]) -> Dict:
        """커밋 분석"""
        analysis = {
            'total_commits': len(commits),
            'by_type': {},
            'by_scope': {},
            'breaking_changes': [],
            'version_bump': 'patch',
            'importance_score': 0
        }
        
        # 타입별 통계
        for commit in commits:
            commit_type = commit.type
            if commit_type not in analysis['by_type']:
                analysis['by_type'][commit_type] = 0
            analysis['by_type'][commit_type] += 1
            
            # 스코프별 통계
            if commit.scope:
                if commit.scope not in analysis['by_scope']:
                    analysis['by_scope'][commit.scope] = 0
                analysis['by_scope'][commit.scope] += 1
            
            # Breaking Change 수집
            if commit.breaking_change:
                analysis['breaking_changes'].append(commit)
            
            # 중요도 점수 계산
            importance = self.importance_levels.get(commit_type, 1)
            analysis['importance_score'] += importance
        
        # 버전 증가 결정
        if analysis['breaking_changes']:
            analysis['version_bump'] = 'major'
        elif 'feat' in analysis['by_type']:
            analysis['version_bump'] = 'minor'
        
        return analysis
    
    def generate_changelog(self, commits: List[ConventionalCommit], version: Optional[str] = None) -> str:
        """CHANGELOG 생성"""
        if not commits:
            return "# CHANGELOG\n\n변경사항이 없습니다.\n"
        
        # 분석 수행
        analysis = self.analyze_commits(commits)
        
        # 헤더 생성
        changelog = f"# CHANGELOG\n\n"
        
        if version:
            changelog += f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        # Breaking Changes
        if analysis['breaking_changes']:
            changelog += "### ⚠️ BREAKING CHANGES\n\n"
            for commit in analysis['breaking_changes']:
                changelog += f"- **{commit.type}**: {commit.description}\n"
                if commit.footer:
                    changelog += f"  - {commit.footer.replace('BREAKING CHANGE:', '').strip()}\n"
            changelog += "\n"
        
        # 타입별 그룹화
        for commit_type in ['feat', 'fix', 'perf', 'refactor', 'docs', 'style', 'test', 'build', 'ci', 'chore']:
            type_commits = [c for c in commits if c.type == commit_type and not c.breaking_change]
            
            if type_commits:
                type_name = self.allowed_types.get(commit_type, commit_type)
                changelog += f"### {type_name.title()}\n\n"
                
                for commit in type_commits:
                    scope_text = f"**{commit.scope}**: " if commit.scope else ""
                    changelog += f"- {scope_text}{commit.description}\n"
                
                changelog += "\n"
        
        # 통계 정보
        changelog += "## 📊 통계\n\n"
        changelog += f"- **총 커밋 수**: {analysis['total_commits']}개\n"
        changelog += f"- **버전 증가**: {analysis['version_bump']}\n"
        changelog += f"- **중요도 점수**: {analysis['importance_score']}\n"
        
        if analysis['by_type']:
            changelog += f"- **타입별 분포**: {', '.join([f'{k}({v})' for k, v in analysis['by_type'].items()])}\n"
        
        return changelog
    
    def get_current_version(self) -> Optional[str]:
        """현재 버전 가져오기"""
        try:
            # package.json에서 버전 확인
            if os.path.exists('package.json'):
                with open('package.json', 'r') as f:
                    data = json.load(f)
                    return data.get('version')
            
            # pyproject.toml에서 버전 확인
            if os.path.exists('pyproject.toml'):
                with open('pyproject.toml', 'r') as f:
                    content = f.read()
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if version_match:
                        return version_match.group(1)
            
            # setup.py에서 버전 확인
            if os.path.exists('setup.py'):
                with open('setup.py', 'r') as f:
                    content = f.read()
                    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                    if version_match:
                        return version_match.group(1)
            
            # Git 태그에서 최신 버전 확인
            result = subprocess.run(['git', 'tag', '--sort=-version:refname'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                tags = result.stdout.strip().split('\n')
                # 버전 태그만 필터링
                version_tags = [tag for tag in tags if re.match(r'^v?\d+\.\d+\.\d+', tag)]
                if version_tags:
                    return version_tags[0].lstrip('v')
            
            return "0.1.0"  # 기본 버전
            
        except Exception as e:
            print(f"버전 확인 중 오류: {e}")
            return "0.1.0"
    
    def bump_version(self, current_version: str, bump_type: str) -> str:
        """버전 증가"""
        try:
            # 버전 파싱
            version_parts = current_version.split('.')
            major, minor, patch = int(version_parts[0]), int(version_parts[1]), int(version_parts[2])
            
            # 버전 증가
            if bump_type == 'major':
                major += 1
                minor = 0
                patch = 0
            elif bump_type == 'minor':
                minor += 1
                patch = 0
            elif bump_type == 'patch':
                patch += 1
            
            return f"{major}.{minor}.{patch}"
            
        except Exception as e:
            print(f"버전 증가 중 오류: {e}")
            return current_version
    
    def create_git_tag(self, version: str, message: Optional[str] = None) -> bool:
        """Git 태그 생성"""
        try:
            tag_name = f"v{version}"
            tag_message = message or f"Release version {version}"
            
            # 태그 생성
            subprocess.run(['git', 'tag', '-a', tag_name, '-m', tag_message], check=True)
            
            # 태그 푸시
            subprocess.run(['git', 'push', 'origin', tag_name], check=True)
            
            print(f"✅ Git 태그 생성 완료: {tag_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Git 태그 생성 실패: {e}")
            return False
    
    def create_github_release(self, version: str, changelog: str, draft: bool = False) -> bool:
        """GitHub 릴리즈 생성 (GitHub CLI 사용)"""
        try:
            # GitHub CLI 설치 확인
            result = subprocess.run(['gh', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ GitHub CLI가 설치되지 않았습니다. 수동으로 릴리즈를 생성하세요.")
                return False
            
            tag_name = f"v{version}"
            release_title = f"Release {version}"
            
            # 임시 파일에 CHANGELOG 저장
            temp_file = f"CHANGELOG_{version}.md"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(changelog)
            
            # GitHub 릴리즈 생성
            cmd = ['gh', 'release', 'create', tag_name, '--title', release_title, '--notes-file', temp_file]
            if draft:
                cmd.append('--draft')
            
            subprocess.run(cmd, check=True)
            
            # 임시 파일 삭제
            os.remove(temp_file)
            
            print(f"✅ GitHub 릴리즈 생성 완료: {tag_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ GitHub 릴리즈 생성 실패: {e}")
            return False

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Conventional Commits 자동화 도구')
    parser.add_argument('--validate', action='store_true', help='커밋 메시지 유효성 검사')
    parser.add_argument('--generate-changelog', action='store_true', help='CHANGELOG 생성')
    parser.add_argument('--create-release', action='store_true', help='릴리즈 생성')
    parser.add_argument('--since', help='시작 날짜 (YYYY-MM-DD)')
    parser.add_argument('--until', help='종료 날짜 (YYYY-MM-DD)')
    parser.add_argument('--version', help='릴리즈 버전')
    parser.add_argument('--draft', action='store_true', help='드래프트 릴리즈 생성')
    parser.add_argument('--output', help='출력 파일명')
    
    args = parser.parse_args()
    
    manager = ConventionalCommitsManager()
    
    if args.validate:
        # 커밋 메시지 유효성 검사
        print("🔍 커밋 메시지 유효성 검사 중...")
        
        # 최근 커밋 메시지 가져오기
        try:
            result = subprocess.run(['git', 'log', '-1', '--pretty=%B'], capture_output=True, text=True)
            if result.returncode == 0:
                commit_msg = result.stdout.strip()
                is_valid, errors = manager.validate_commit_message(commit_msg)
                
                if is_valid:
                    print("✅ 커밋 메시지가 Conventional Commits 형식입니다.")
                else:
                    print("❌ 커밋 메시지 오류:")
                    for error in errors:
                        print(f"  - {error}")
            else:
                print("❌ Git 커밋을 가져올 수 없습니다.")
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    if args.generate_changelog:
        # CHANGELOG 생성
        print("📝 CHANGELOG 생성 중...")
        
        commits = manager.get_git_commits(args.since, args.until)
        if commits:
            changelog = manager.generate_changelog(commits, args.version)
            
            output_file = args.output or 'CHANGELOG.md'
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(changelog)
            
            print(f"✅ CHANGELOG 생성 완료: {output_file}")
        else:
            print("❌ 생성할 커밋이 없습니다.")
    
    if args.create_release:
        # 릴리즈 생성
        print("🚀 릴리즈 생성 중...")
        
        # 현재 버전 확인
        current_version = manager.get_current_version()
        print(f"현재 버전: {current_version}")
        
        # 최근 커밋 분석
        commits = manager.get_git_commits(args.since, args.until)
        if not commits:
            print("❌ 생성할 릴리즈가 없습니다.")
            return 1
        
        analysis = manager.analyze_commits(commits)
        
        # 새 버전 계산
        if args.version:
            new_version = args.version
        else:
            new_version = manager.bump_version(current_version, analysis['version_bump'])
        
        print(f"새 버전: {new_version} ({analysis['version_bump']} 증가)")
        
        # CHANGELOG 생성
        changelog = manager.generate_changelog(commits, new_version)
        
        # Git 태그 생성
        if manager.create_git_tag(new_version, f"Release {new_version}"):
            # GitHub 릴리즈 생성
            manager.create_github_release(new_version, changelog, args.draft)
        
        # CHANGELOG 파일 저장
        with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
            f.write(changelog)
        
        print("✅ 릴리즈 생성 완료!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
