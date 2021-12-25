self.ld.downcpu(self.index)
self.set_guid(self.params.get("guid", ''))
self.kill_qq()
self.open_qq()
self.input_account_password(self.params.get(
    "account", ''), self.params.get("password", ''))
self.login_qq()
