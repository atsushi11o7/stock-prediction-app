# == Schema Information
#
# Table name: sectors
#
#  id         :bigint           not null, primary key
#  name       :string           not null
#  created_at :datetime         not null
#  updated_at :datetime         not null
#
# Indexes
#
#  index_sectors_on_name  (name) UNIQUE
#

# セクター（業種大分類）を管理するモデル
class Sector < ApplicationRecord
  has_many :industries, dependent: :destroy
  has_many :companies, dependent: :nullify

  validates :name, presence: true, uniqueness: true

  scope :ordered, -> { order(:name) }
end
