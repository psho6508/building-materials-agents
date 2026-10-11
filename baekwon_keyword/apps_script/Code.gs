// 구글 Apps Script 웹앱 — GitHub Actions가 서비스 계정 대신 이 웹앱을 통해
// 본인(psho6508) 계정 권한으로 구글 드라이브를 읽고/쓰게 한다.
// (서비스 계정은 저장용량이 0GB라 개인 Gmail 드라이브에 새 파일을 못 만든다 —
//  이 웹앱은 배포한 사람의 권한으로 실행되므로 그 문제가 없다.)
//
// 설정:
// 1. script.google.com → 새 프로젝트 → 이 코드 붙여넣기
// 2. 프로젝트 설정(톱니바퀴) → 스크립트 속성 → 속성 추가:
//    이름 SHARED_SECRET, 값은 GitHub Secrets의 APPS_SCRIPT_SECRET과 동일한 값으로
//    (이 .gs 파일은 공개 저장소에 커밋되므로 비밀값을 코드에 직접 적지 않는다)
// 3. 배포 → 새 배포 → 유형: 웹 앱 → 실행 대상: 나 → 액세스 권한: 모든 사용자 → 배포
//    처음 배포 시 권한 승인 화면이 뜨면 본인 계정으로 승인
//    (고급 → 안전하지 않음으로 이동, 눌러도 됨 — 본인이 만든 스크립트이므로 안전)
// 코드를 수정한 뒤에는 "배포 → 배포 관리 → 기존 배포 수정 → 새 버전"으로
// 업데이트해야 URL이 바뀌지 않는다.
//
// 액션 (data.action):
// - "save_manuscript" (기본값, 생략 가능): title/text/folderId → 구글 문서로 저장, {url}
// - "list_footage_folders": folderId → 그 폴더 바로 아래 하위 폴더 이름/링크 목록, {folders:[{id,name,url}]}
// - "list_folder_files": folderId → 그 폴더 안 파일(이미지/영상) 이름/링크/타입 목록, {files:[{name,url,mimeType}]}

function doPost(e) {
  var SHARED_SECRET = PropertiesService.getScriptProperties().getProperty("SHARED_SECRET");

  var data = JSON.parse(e.postData.contents);
  if (data.secret !== SHARED_SECRET) {
    return _json({ error: "unauthorized" });
  }

  try {
    var action = data.action || "save_manuscript";
    if (action === "list_footage_folders") return _json(listFootageFolders(data.folderId));
    if (action === "list_folder_files") return _json(listFolderFiles(data.folderId));
    return _json(saveManuscript(data.title, data.text, data.folderId));
  } catch (err) {
    return _json({ error: String(err) });
  }
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function saveManuscript(title, text, folderId) {
  var folder = DriveApp.getFolderById(folderId);
  var doc = DocumentApp.create(title);
  var body = doc.getBody();
  body.setText(text);
  doc.saveAndClose();

  var file = DriveApp.getFileById(doc.getId());
  folder.addFile(file);
  DriveApp.getRootFolder().removeFile(file);

  return { url: doc.getUrl() };
}

function listFootageFolders(folderId) {
  var parent = DriveApp.getFolderById(folderId);
  var it = parent.getFolders();
  var folders = [];
  while (it.hasNext()) {
    var f = it.next();
    folders.push({ id: f.getId(), name: f.getName(), url: f.getUrl() });
  }
  return { folders: folders };
}

function listFolderFiles(folderId) {
  var folder = DriveApp.getFolderById(folderId);
  var it = folder.getFiles();
  var files = [];
  while (it.hasNext()) {
    var f = it.next();
    files.push({ name: f.getName(), url: f.getUrl(), mimeType: f.getMimeType() });
  }
  return { files: files };
}
