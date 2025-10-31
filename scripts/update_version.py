#!/usr/bin/env python3
"""
Script to update Zephyr application VERSION file based on git tags.
This script is automatically called during west build.

Usage:
    python update_version.py [app_name] [version_file_path]
    python update_version.py minimal_dcs_cam apps/minimal_dcs_cam/VERSION
"""
import argparse
import datetime
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def get_git_version():
    """Get version from git describe using app-specific tag pattern."""
    try:
        # Run git describe with app-specific tag pattern and --dirty flag
        result = subprocess.run([
            "git", "describe", "--long", "--tags", "--dirty"
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not get version from git tags: {e}", file=sys.stderr)
        return None


def parse_version(git_desc, default_extraversion="dev"):
    """Parse git describe output into version components."""
    if not git_desc:
        # Fallback version if no tags found
        raise ValueError(f"No git tags found. Please create a tag in the format 'vx.x.x'.")

    # Parse format: minimal_dcs_cam-v1.2.3-4-gabcdef or minimal_dcs_cam-v1.2.3-4-gabcdef-dirty
    pattern = rf"v(\d+).(\d+).(\d+)-(\d+)-g([0-9a-f]+)(-dirty)?"
    match = re.match(pattern, git_desc)

    if not match:
        print(f"Warning: Tag format not recognized: {git_desc}", file=sys.stderr)
        print(f"Expected format: fw-minimal_dcs_cam-v1.2.3", file=sys.stderr)
        raise ValueError(f"Invalid tag format: {git_desc}")

    major, minor, patch, commits_since, commit_hash, dirty_suffix = match.groups()

    # Determine extraversion based on commits since tag and dirty status
    if dirty_suffix:
        extraversion = f"dirty-g{commit_hash}"
    elif int(commits_since) > 0:
        extraversion = f"{default_extraversion}-g{commit_hash}"
    else:
        extraversion = ""

    return int(major), int(minor), int(patch), int(commits_since), extraversion

def find_unreleased_heading(content):
    """Find the '## [Unreleased]' heading and return a match object with groups."""
    # Pattern matches headings like "## [Unreleased]" or "## Unreleased"
    # Groups: hashes (the ##), label1 ([Unreleased]), label2 (Unreleased without brackets)
    pattern = r'^(?P<hashes>#+)\s*(?:(?P<label1>\[Unreleased\])|(?P<label2>Unreleased)).*$'
    return re.search(pattern, content, re.MULTILINE | re.IGNORECASE)


def update_changelog(changelog_path: Path, version: str, date_str: str | None = None) -> bool:
    """
    Update the changelog file at changelog_path.
    Returns True if file was changed, False otherwise.
    """
    if not changelog_path.exists():
        print(f"Changelog file not found: {changelog_path}", file=sys.stderr)
        return False

    if date_str is None:
        date_str = datetime.date.today().isoformat()

    text = changelog_path.read_text(encoding="utf-8")
    m = find_unreleased_heading(text)
    if not m:
        print("No 'Unreleased' heading found in changelog.", file=sys.stderr)
        return False

    hashes = m.group("hashes")
    used_bracket = bool(m.group("label1"))

    # Build headings
    # Keep bracketed style for the new Unreleased heading if original used brackets.
    new_unreleased_heading = f"{hashes} [Unreleased]" if used_bracket else f"{hashes} Unreleased"
    # Use bracketed version for released heading (common style)
    released_heading = f"{hashes} [{version}] - {date_str}"

    # Replace only the first occurrence: insert new Unreleased above the renamed released heading.
    start, end = m.span()
    before = text[:start]
    after = text[end:]
    # Keep the content that followed the original Unreleased heading as-is, but it now belongs to released_heading.
    new_text = before + new_unreleased_heading + "\n\n" + released_heading + after

    if new_text == text:
        print("Changelog unchanged.", file=sys.stderr)
        return False

    # atomic write
    fd, tmpname = tempfile.mkstemp(dir=changelog_path.parent, prefix=".changelog.", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        os.replace(tmpname, str(changelog_path))
    finally:
        if os.path.exists(tmpname):
            try:
                os.remove(tmpname)
            except Exception:
                pass

    return True


def determine_version_bump(latest_tag, major, minor, patch):
    """Determine version bump type based on merge commits since latest tag."""
    try:
        merges = subprocess.run(
            ["git", "log", f"{latest_tag}..HEAD", "--merges", "--pretty=format:'%H %s'"],
            capture_output=True, text=True, check=True
        ).stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error reading git log: {e}", file=sys.stderr)
        sys.exit(1)

    bump_type = None
    for merge in merges:
        sha, message = merge.strip("'").split(' ', 1)
        lower_merge = message.lower()
        if any(k in lower_merge for k in ['feature/', 'dev/']):
            bump_type = "minor"
            print(f"Processing merge commit: {message} -> bumping minor")
            break  # Minor bump takes precedence
        elif any(k in lower_merge for k in ['fix/', 'refactor/']):
            bump_type = "patch"
            print(f"Processing merge commit: {message} -> bumping patch")

    if not bump_type:
        return None

    major, minor, patch = int(major), int(minor), int(patch)
    if bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1

    return major, minor, patch


def prepare_tag_message_from_changelog(changelog_path, new_version):
    """Prepare a git tag message from the changelog for the given version."""
    tag_message = f"Release {new_version}"
    if changelog_path and changelog_path.exists():
        try:
            text = changelog_path.read_text(encoding="utf-8")
            # Find the section for the new version
            pattern = rf'^## \[{re.escape(new_version)}\]'
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                start = match.end()
                # Find the next heading
                next_heading = re.search(r'^## ', text[start:], re.MULTILINE)
                if next_heading:
                    section = text[start:start + next_heading.start()].strip()
                else:
                    section = text[start:].strip()
                if section:
                    tag_message = f"Release {new_version}\n\n{section}"
        except Exception as e:
            print(f"Warning: Could not read changelog for tag message: {e}", file=sys.stderr)
    return tag_message


def bump_version(major, minor, patch, changelog_path=None):
    """Bump the version based on the latest git tag and merge commit messages."""

    tag_prefix = f'v'
    latest_tag = f"{tag_prefix}{major}.{minor}.{patch}"
    # Get merge commit messages since latest tag

    if not major == minor == patch == 0:
        bumped_version = determine_version_bump(latest_tag, major, minor, patch)
        if bumped_version is None:
            print("No version bump needed based on git history.", file=sys.stderr)
            return None
        major, minor, patch = bumped_version

    new_version = f"{major}.{minor}.{patch}"
    new_tag = f"{tag_prefix}{new_version}"
    print(f"Bumping version to: {new_tag}")

    # Update changelog if it exists (use custom path or default)
    if changelog_path is None:
        changelog_path = "CHANGELOG.md"

    if changelog_path.exists():
        print(f"Updating changelog: {changelog_path}")
        if update_changelog(changelog_path, new_version):
            print(f"Changelog updated: Unreleased -> {new_version}")
            # Stage the changelog changes
            subprocess.run(["git", "add", str(changelog_path)], check=True)
            subprocess.run(["git", "commit", "-m", f"release: update changelog for {new_version}"], check=True)
        else:
            print("Changelog was not updated (no changes or no Unreleased section)")
    else:
        print(f"No changelog found at {changelog_path}, skipping changelog update")

    # Prepare tag message from changelog
    tag_message = prepare_tag_message_from_changelog(changelog_path, new_version)

    # Create the git tag
    subprocess.run(["git", "tag", "-m", tag_message, new_tag], check=True)
    # subprocess.run(["git", "push", "origin", new_tag], check=True)
    return new_tag


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update Zephyr application VERSION file based on git tags",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_version.py minimal_dcs_cam apps/minimal_dcs_cam/VERSION
  python update_version.py people_counter apps/people_counter/VERSION
  python update_version.py minimal_dcs_cam apps/minimal_dcs_cam/VERSION --extraversion beta
  
  Notes:
  - 'dirty-g<hash>' is automatically added when working directory has uncommitted changes
  - '--extraversion-g<hash>' is used for commits since last tag (default: dev-g<hash>)
  - <hash> is the short commit SHA for traceability
        """
    )

    parser.add_argument(
        "--extraversion",
        default="dev",
        help="EXTRAVERSION to use for development builds (when commits exist since last tag, default: dev). Note: 'dirty' is automatically used when working directory has uncommitted changes."
    )

    parser.add_argument(
        "--bump",
        default=False,
        action="store_true",
        help="Bump the version automatically (default: False). This will create a new tag based on the latest tag."
    )

    parser.add_argument(
        "--changelog",
        type=Path,
        help="Path to CHANGELOG.md file (default: FOLDER/CHANGELOG.md)"
    )

    return parser.parse_args()


def main():
    """Main function to update VERSION file from git tags."""
    args = parse_args()

    # Get version from git
    git_desc = get_git_version()

    # Parse version components
    if not git_desc:
        major, minor, patch, tweak, extraversion = 0, 0, 0, 0, args.extraversion
    else:
        major, minor, patch, tweak, extraversion = parse_version(git_desc, args.extraversion)

    if args.bump:
        bump_version(major, minor, patch, args.changelog)
        return


if __name__ == "__main__":
    main()
