# == Schema Information
#
# Table name: industries
#
#  id         :bigint           not null, primary key
#  name       :string           not null
#  sector_id  :bigint           not null
#  created_at :datetime         not null
#  updated_at :datetime         not null
#
# Indexes
#
#  index_industries_on_sector_id           (sector_id)
#  index_industries_on_sector_id_and_name  (sector_id,name) UNIQUE
#
# Foreign Keys
#
#  fk_rails_...  (sector_id => sectors.id)
#

# 業種（業種小分類）を管理するモデル
class Industry < ApplicationRecord
  belongs_to :sector
  has_many :companies, dependent: :nullify

  validates :name, presence: true
  validates :name, uniqueness: { scope: :sector_id }

  scope :ordered, -> { order(:name) }
  scope :by_sector, ->(sector) { where(sector: sector) }

  # セクター名と業種名を組み合わせた完全な業種名を返す
  #
  # @return [String] 完全な業種名（例: "情報・通信業 / インターネット付随サービス"）
  def full_name
    "#{sector.name} / #{name}"
  end
end
